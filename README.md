# Ragdoll Lab VR

A browser physics sandbox for VR headsets and desktop. Spawn crates, bombs, carts and customisable ragdoll NPCs, then grab, throw, freeze, tie up and blow up everything across five maps.

Play: open `index.html` over HTTPS (GitHub Pages works) in a WebXR browser such as the Meta Quest Browser and press **Enter VR**, or press **Play on desktop** on a computer.

## Weapons

Twelve weapons live in the Weapons tab of the menu: Pistol, Shotgun, SMG, Rocket Launcher, Grenade, Crossbow, Sword, Baseball Bat, Sledgehammer, Flamethrower, Lightning Gun and Freeze Ray. They are physical objects, so you can drop, throw and pick them up again. Melee weapons hit with real swings. Headshots do double damage, burning NPCs panic, and lightning arcs between nearby NPCs.

## Gore

NPCs have a skeleton (skull, spine, ribs, pelvis and limb bones) and organs (brain, lungs, heart, liver, stomach, kidneys and intestines) inside them. Bullets, blades, explosions and very hard impacts take chunks out of the body so you can see inside, throw out bits of meat and leave blood on the ground. Wounded NPCs keep bleeding for a while. Blunt hits, falls and being thrown into things leave bruises that darken with repeated hits, and fire chars the skin. Reviving an NPC heals it. Set **World → Gore** to Full, Bruises only or Off. **Clean up blood** removes the mess.

## Weapon Workshop

The Workshop tab lets you make your own weapon in five steps:

1. **Draw** it in the air (VR: hold the trigger; desktop: drag with the left mouse, right-drag to look around). Pick colours and thickness, undo strokes with Y or Z.
2. **Type:** ranged or melee. Ranged weapons pick an ammo type (bullets, laser, rockets, scatter, flames, lightning, sticky bolts, freeze shot, grenades or bouncy balls) and a fire mode (single shot, burst of 3 or full auto).
3. **Grip:** mark where your hand holds it.
4. **Damage:** for ranged, mark one or more barrel tips (up to 8). Each barrel fires along the line you drew at that tip, and they all fire together. Mark a tip again to remove it. For melee, paint the part that hurts. Only the painted part deals damage.
5. **Tune:** give it a name and set its stats. Ranged: damage, fire rate, knockback, accuracy, shots per barrel, projectile speed, blast size, recoil, shot colour and weight. Melee: blunt or sharp edge, a hit effect (fire, freeze, electric shock, explosion or shockwave), damage, knockback, effect size and weight.

Finished weapons are equipped straight away and saved in your browser, listed under "Your weapons". Press ⚙ next to a saved weapon to change its ammo, fire mode, name and stats later.

## Controls

**VR:** trigger = use tool, grip = grab and throw, left stick = walk, right stick = turn (up/down while holding reels the object in or out), X (or left stick click) = menu, which floats in front of you: point and pull the trigger, or poke a button with the controller tip, A = next tool, B = next spawn item, Y = undo.

**Desktop:** WASD move, Shift run, Space jump, left click = use tool, right click or E = grab, mouse wheel = push or pull the held object, R = rotate it, 1-0 = tools, Q = next spawn item, Tab = menu, F = drop weapon, Z = undo, T = slow motion, G = zero gravity, P = pause.

Built with three.js and cannon-es, loaded from the jsDelivr CDN. No build step.


