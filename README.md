# Ragdoll Lab VR

A browser physics sandbox for VR headsets and desktop. Spawn crates, bombs, carts and customisable ragdoll NPCs, then grab, throw, freeze, tie up and blow up everything across five maps.

Play: open `index.html` over HTTPS (GitHub Pages works) in a WebXR browser such as the Meta Quest Browser and press **Enter VR**, or press **Play on desktop** on a computer.

## Weapons

Twelve weapons live in the Weapons tab of the menu: Pistol, Shotgun, SMG, Rocket Launcher, Grenade, Crossbow, Sword, Baseball Bat, Sledgehammer, Flamethrower, Lightning Gun and Freeze Ray. They are physical objects, so you can drop, throw and pick them up again. Melee weapons hit with real swings. Headshots do double damage, burning NPCs panic, and lightning arcs between nearby NPCs.

## Ragdoll Maker

Press **Ragdoll maker** in the NPC tab to design your own ragdolls. **Shape** sets the overall size and the width of the shoulders, torso length, belly, arm length and leg length. **Head** sets head size, round, boxy or tall heads, neck length (up to a giraffe neck), a face (normal, happy, angry, shocked, sleepy, cyclops, shades or blank), a hat (cap, top hat, crown, helmet, viking helmet, party hat, horns or halo) and hair (short, long, mohawk, afro or ponytail). **Colours** paints the shirt, trousers, skin, shoes, hat and hair. **Build** changes arm and leg thickness, weight, muscles (weak ones can barely stand up), joints (stiff to noodle) and walking speed. A front and side view shows the design to scale with its height and weight. **Saved** lets you name and save designs in your browser, and has eight starters to begin from: Tiny, Giant, Noodle, Brute, Bobblehead, Long neck, Robot and King. Press **Spawn it** and place it with the Spawner. Custom ragdolls walk, fight, bleed and fall apart like normal ones, and other players see them online.

## Online

The Online tab puts you in a shared world with other players, on PC or in VR, using Supabase Realtime (no accounts or database needed). **Create room** gives you a four-letter code to share, **Join with a code** takes that code, and **Join public lobby** puts you in with anyone else who's on. You can also send a link ending in `?room=CODE`. Pick a name and colour first. Everyone sees each other as a coloured avatar with a name tag, and spawning, grabbing, throwing, shooting, explosions, wounds, balloons, ropes, map changes, gravity and time are all shared. Whatever you grab is simulated on your computer until someone else grabs it. With **PvP** on (the default), weapons, thrown objects and explosions hurt other players. Running out of health knocks you out for three seconds, then you respawn. The first person in a room is the host and owns the map. If the host leaves, someone else takes over.

## Duel

The Duel tab sets up a one-on-one fight against a ragdoll that fights back. Pick its weapon (fists, sword, bat, sledgehammer, pistol, shotgun, SMG, crossbow, rocket launcher, flamethrower, lightning gun or random), the difficulty (Easy, Normal, Hard or Brutal) and the weapon you start with (any of the 12, or one you drew). The opponent closes in to swing at you or keeps its distance and strafes while shooting. You have 100 health, shown at the top of the screen (in VR, low in your view), and the screen flashes red when you are hit. Objects between you and the opponent block its shots, moving makes it miss more, and explosions hurt you, your own included. Knock it out to win, then pick Rematch or Leave duel.

## Gore

NPCs have a skeleton (skull, spine, ribs, pelvis and limb bones) and organs (brain, lungs, heart, liver, stomach, kidneys and intestines) inside them. Bullets, blades, explosions and very hard impacts take chunks out of the body so you can see inside, throw out bits of meat and leave blood on the ground. Wounded NPCs keep bleeding for a while. Blunt hits, falls and being thrown into things leave bruises that darken with repeated hits, and fire chars the skin. Reviving an NPC heals it. Set **World → Gore** to Full, Bruises only or Off. **Clean up blood** removes the mess.

## Weapon Workshop

The Workshop tab lets you make your own weapon in five steps:

1. **Draw** it in the air (VR: hold the trigger; desktop: drag with the left mouse, right-drag to look around). Draw freehand, or pick a shape tool (line, box, ball, tube, cone or ring) and drag it out to size. Pick colours and thickness, undo with Y or Z.
2. **Type:** ranged or melee. Ranged weapons pick an ammo type (bullets, laser, rockets, scatter, flames, lightning, sticky bolts, freeze shot, grenades or bouncy balls) and a fire mode (single shot, burst of 3 or full auto).
3. **Grip:** mark where your hand holds it.
4. **Damage:** for ranged, mark one or more barrel tips (up to 8). Each barrel fires along the line you drew at that tip, and they all fire together. Mark a tip again to remove it. For melee, paint the part that hurts. Only the painted part deals damage.
5. **Tune:** give it a name and set its stats. Ranged: damage, fire rate, knockback, accuracy, shots per barrel, projectile speed, blast size, recoil, shot colour and weight. Melee: the swing animation (side slash, backhand, overhead chop, uppercut, stab, spin, a three-hit flurry or a combo that alternates), swing speed and size (with a preview), blunt or sharp edge, a hit effect (fire, freeze, electric shock, explosion or shockwave), damage, knockback, effect size and weight.

Finished weapons are equipped straight away and saved in your browser, listed under "Your weapons". Press ⚙ next to a saved weapon to change its ammo, fire mode, name and stats later.

## Controls

**VR:** trigger = use tool, grip = grab and throw, left stick = walk, right stick = turn (up/down while holding reels the object in or out), X (or left stick click) = menu, which floats in front of you: point and pull the trigger, or poke a button with the controller tip, A = next tool, B = next spawn item, Y = undo.

**Desktop:** WASD move, Shift run, Space jump, left click = use tool, right click or E = grab, mouse wheel = push or pull the held object, R = rotate it, 1-0 = tools, Q = next spawn item, Tab = menu, F = drop weapon, Z = undo, T = slow motion, G = zero gravity, P = pause.

Built with three.js and cannon-es, loaded from the jsDelivr CDN. No build step.


