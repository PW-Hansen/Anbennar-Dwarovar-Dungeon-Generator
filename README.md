## XML converter v1.0
Takes in the (uncompressed) XML output of a draw.io diagram for a Dwarovar Dungeon and generates (most of) the event code, as well as a localization file for the generated events.

One such XML output can be found in the examples folder, along with a PNG of the corresponding diagram. Credit to Thurinsen for these.

# draw.io guidelines
The following should be adhered to when creating the draw.io diagram:
* Delete all boxes which are not intended as events for the dungeon.
* Make sure that all arrows originate from an option and end at the head/title of an event, and that it is attached to one of the connection points for the latter.
* Stick to the standards laid out in the example: Green for success, red for failure (with the title "Game Over" if it should result in a premature end of the dungeon expedition), orange-ish for successfully completing the floor, and so on.
* Options with a success/fail outcomes should have either "(E)", "(M)", or "(H)" at the end to denote difficulty, currently corresponding to a base success chance of 80%, 60%, and 40% respectively. Alternatively, a base success chance can be set by ending the option text with "(X)", where X is an integer. If no parenthesis is present, the script will set the base success chance to easy.

# Script usage
* Run the script.
* Provide a name, a starting ID, an outpit file name, and then copy-paste the contents of an uncompressed XML-file for the dungeon.
* Adjust the party statistics sliders as desired.
* Click run the program.
* If an error is encountered, "Ready to run" will chance to "Something went wrong. Check that Starting ID is a number. Otherwise, contact Magnive on Discord.
* Otherwise, the script will have written the event and localization files to an output folder.

Things the script does *not* do:
* Handles triggers for multi-description events. This must currently be done manually.
* Verify that all events are part of a floor.
* Verify that events are properly connected.
