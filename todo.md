 This project is a personal briefing and debriefing tool for a 4way formation skydiving team.

 Start with the given scoring.py and change it with the instructions below.

 What is needed.

 First of all a video from a videographer. Mostley from a GoPro should be loaded.
 Then a Start Frame and a end frame should be set already in the tool.
 The Tool should then cut the video with the start and end frame.
 No sound is needed.

 This video should than be possible to brief on
 
 Needed Features
 It should be possible to enter the formations for the jump.
 There should also be a time line to pick a position in the video.
 
 
 Needed Events. 
 1. Start the timer. For 4way this is mostley 35sec in competition but can be reduced to 20sec. For training this can also be 60sec
 2. After starting the timer the points need to be counted or busted. 
 3. There should be a timeline where the points are represented ether aproved or busted.
 4. It should be possible to also indicate when the formation was finished an when the key was given.


Needed Fixes:
- [x] 1. FAI blocks are two separate points so in the points list its needed to show the first and the second point of a block not just rotate the entered formations. *(Done: `expand_draw_to_points_sequence` breaks blocks into `-1` and `-2`, cycles rotate through full sequence).*
- [x] 2. Add a detailed description how count point, point finished and point keyed is working together and how the times are shown in the point list. Check if this works always correctly. It seems to me there are misscalculations but im not sure how it should work. *(Done: Comprehensive documentation added to README.md and interactive F1 Dialog. Timing math fixed to prevent masking errors and highlight negative delta mistakes with ⚠️).*

Needed Extended Features:
- [x] 1. After selecting a given point it should be possible to set the finished and key time. *(Done: Point selection mode via timeline click, table row click, or double click; action bar and F/K shortcuts update selected point).*
- [x] 2. An already saved debrief should be editable. For example change the draw. *(Done: `🔄 Draw anwenden` button updates formation codes of all existing points while preserving timestamps, keys, status and notes).*
3. Create a Draw generator where a selected number of rounds draws are generated following the FAI AAA rules for a draw.
4. Create a Training Database where all briefings are stored and all trained formations and randoms.
5. Consider the Training Database for the Draw generator so that blocks and randoms are used they are least trained.
6. Show the pictures of the draw provided from the Rythm XP pdfs
7. 

 
 
