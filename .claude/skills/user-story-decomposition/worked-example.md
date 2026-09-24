# User Story Decomposition — worked example

Read to see the expected shape of the output.

## Worked example (condensed)

Epic: *Playing-card-game app — gameplay.*
Actor: *player.*
Format: **User story** — single actor, no meaningfully distinct alternate paths worth
pre-documenting as a use case.

> Story: As a player, I want to start a new game and select the card game variation, so that
> I can play the game I'm in the mood for.
> Acceptance Criteria:
> - A list of available game variations is shown.
> - The selected variation's rules and mechanics are what's enforced for the rest of the game.

> Story: As a player, I want to view and interact with my hand during the game, so that I can
> make my moves.
> Acceptance Criteria:
> - The player's hand is shown with clear visuals and card information.
> - The player can select and play a card from their hand.
> - An invalid move is rejected with feedback, not silently ignored.

Multiplayer (invite friends, join public rooms, in-game chat, leaderboards) and customization
(deck/card-back appearance) are separate feature groups — each gets its own story set rather
than folding into gameplay's.
