# Ragdoll Lab VR

A browser physics sandbox for VR headsets and desktop. Spawn crates, bombs, carts and customisable ragdoll NPCs, then grab, throw, freeze, tie up and blow up everything across five maps.

Play: open `index.html` over HTTPS (GitHub Pages works) in a WebXR browser such as the Meta Quest Browser and press **Enter VR**, or press **Play on desktop** on a computer.

## Weapons

Twelve weapons live in the Weapons tab of the menu: Pistol, Shotgun, SMG, Rocket Launcher, Grenade, Crossbow, Sword, Baseball Bat, Sledgehammer, Flamethrower, Lightning Gun and Freeze Ray. They are physical objects, so you can drop, throw and pick them up again. Melee weapons hit with real swings. Headshots do double damage, burning NPCs panic, and lightning arcs between nearby NPCs.

## Weapon Workshop

The Workshop tab lets you make your own weapon in four steps:

1. **Draw** it in the air (VR: hold the trigger; desktop: drag with the left mouse, right-drag to look around). Pick colours and thickness, undo strokes with Y or Z.
2. **Type:** ranged (bullets, laser, rockets or scatter, single shot or full auto) or melee.
3. **Grip:** mark where your hand holds it.
4. **Damage:** for ranged, mark the barrel tip where shots come out; for melee, paint the part that hurts. Only the painted part deals damage.

Finished weapons are equipped straight away and saved in your browser, listed under "Your weapons".

## Controls

**VR:** trigger = use tool, grip = grab and throw, left stick = walk, right stick = turn (up/down while holding reels the object in or out), X (or left stick click) = menu, which floats in front of you: point and pull the trigger, or poke a button with the controller tip, A = next tool, B = next spawn item, Y = undo.

**Desktop:** WASD move, Shift run, Space jump, left click = use tool, right click or E = grab, mouse wheel = push or pull the held object, R = rotate it, 1-0 = tools, Q = next spawn item, Tab = menu, F = drop weapon, Z = undo, T = slow motion, G = zero gravity, P = pause.

Built with three.js and cannon-es, loaded from the jsDelivr CDN. No build step.


