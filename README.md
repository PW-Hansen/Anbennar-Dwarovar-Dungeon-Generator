## XML converter v1.1.2
Takes in the (uncompressed) XML output of a draw.io diagram for a Dwarovar Dungeon and generates (most of) the event code, as well as a localization file for the generated events.

One such XML output can be found in the examples folder, along with a PNG of the corresponding diagram. Credit to Thurinsen for these.

# draw.io guidelines
The following should be adhered to when creating the draw.io diagram:
* Delete all boxes which are not intended as events for the dungeon. (Or at least make a clean page for me to export the XML from.)
* Make sure that all arrows originate from an option and end at the head/title of an event, and that it is attached to one of the connection points for the latter.
* Stick to the standards laid out in the example: Green for success, red for failure (with the title "Game Over" if it should result in a premature end of the dungeon expedition), orange-ish for successfully completing the floor, and so on.
* Options with a success/fail outcomes should have either "(E)", "(M)", or "(H)" at the end to denote difficulty, currently corresponding to a base success chance of 80%, 60%, and 40% respectively. Alternatively, a base success chance can be set by ending the option text with "(X)", where X is an integer. If no parenthesis is present, the script will set the base success chance to easy.
* All events must have at least one option which does not require supplies.
* Options with a success outcome must have two outcomes.
* Party statistics changes in options must be seperated by commas.
* Event boxes must be grouped.
* Please do not change the width of any boxes, as this is used to detect which element a textbox is.
# Script usage
* Run the script.
* Provide a name, a starting ID, an outpit file name, and then copy-paste the contents of an uncompressed XML-file for the dungeon.
* Adjust the party statistics sliders as desired.
* Click run the program.
* If an error is encountered, "Ready to run" will chance to "Something went wrong. Check that Starting ID is a number. Otherwise, contact Magnive on Discord.
* Otherwise, the script will have written the event and localization files to an output folder.

Things the script does *not*:
* Handles triggers for multi-description events. This must currently be done manually.
* Verify that all events are part of a floor.


Changelog:
Split assigning events to floors and giving events IDs into two functions, and added a new function between to ensure that floors are in the right order.
Automatically orders text, description, and options when outputting the localization file, rather than trusting that the event_components are in the right order.
Removed integers being represented as floats for party statistics changes, as that messed with the in-game tooltip.
Cleanup with indentation level, threw newline in for ADK effect, and a space which had gotten lost for the party effect changes.
Now supplies the name of events whenever new event IDs are referenced.