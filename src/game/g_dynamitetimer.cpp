#include <bgame/impl.h>

/*
===========================================
g_dynamitetimer.cpp

Per-frame dynamite countdown announcer.
Called from G_RunFrame once per server frame.

Controlled by g_dynamiteTimer cvar:
  0 = disabled
  1 = enabled (default)

Countdown messages are sent:
  - To the planting team: every second for the full duration
  - To the defending team: only in the last 10 seconds

To avoid spamming cp-slots, only one update per second per
dynamite is issued (tracked via grenadeExplodeTime, which is
unused on non-held dynamite entities).
===========================================
*/

extern vmCvar_t g_dynamiteTimer;

// Number of seconds remaining at which defenders start seeing the timer
#define DEFENDER_WARN_SECS  10

void G_RunDynamiteTimers( void ) {
    if( !g_dynamiteTimer.integer )
        return;

    int i, j;

    for( i = MAX_CLIENTS; i < level.num_entities; i++ ) {
        gentity_t *dyn = &g_entities[i];

        if( !dyn->inuse )
            continue;

        // Armed dynamite: classname "dynamite", teamNum < 4, think == G_ExplodeMissile
        if( Q_stricmp( dyn->classname, "dynamite" ) != 0 )
            continue;

        if( dyn->s.teamNum >= 4 )
            continue;   // not yet armed

        if( dyn->think != G_ExplodeMissile )
            continue;

        int msLeft   = dyn->nextthink - level.time;
        if( msLeft <= 0 )
            continue;   // about to explode this frame — let it go

        int secsLeft = ( msLeft + 999 ) / 1000;   // round up

        // grenadeExplodeTime is only set on client entities (held grenades).
        // On a placed dynamite entity it is 0 — safe to reuse as a
        // "last second we announced" tracker.
        if( dyn->grenadeExplodeTime == secsLeft )
            continue;   // already sent this second's update

        dyn->grenadeExplodeTime = secsLeft;

        // Build the message — colour shifts at low time
        const char *color = ( secsLeft <= 5 ) ? "^1" : ( secsLeft <= 10 ) ? "^3" : "^7";
        const char *msg = va( "cp \"%sDynamite: %i second%s!\n\"",
                              color, secsLeft, secsLeft == 1 ? "" : "s" );

        for( j = 0; j < level.maxclients; j++ ) {
            gentity_t *cl = &g_entities[j];

            if( !cl->inuse || !cl->client )
                continue;

            if( cl->client->pers.connected != CON_CONNECTED )
                continue;

            if( cl->client->ps.pm_type == PM_SPECTATOR )
                continue;

            qboolean isPlanter = ( cl->client->sess.sessionTeam == (team_t)dyn->s.teamNum ) ? qtrue : qfalse;

            // Planters always see the timer; defenders see it in the final countdown
            if( isPlanter || secsLeft <= DEFENDER_WARN_SECS ) {
                trap_SendServerCommand( j, msg );
            }
        }
    }
}
