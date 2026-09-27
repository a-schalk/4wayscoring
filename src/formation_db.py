"""
FAI 4-Way Formation Skydiving Dive Pool & Technique Database
Comprehensive database containing all 16 Randoms (A-Q) and 22 Blocks (1-22).
Includes 3D spatial coordinates, body headings, head switches, keys, slot duties,
and coaching methodologies (Rhythm XP, Axis Flight School, Fury Coaching, PACKD).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Flyer3DState:
    """Represents a skydiver's spatial state in 3D relative space."""
    x: float               # X coordinate in inches (-120 to +120)
    y: float               # Y coordinate in inches (-120 to +120)
    z: float               # Z level (-30 to +30, 0 is baseline level)
    heading_deg: float     # Body heading in degrees (0 = North/Top, 90 = East, 180 = South, 270 = West)
    head_turn_deg: float = 0.0  # Head rotation relative to body heading (+ right, - left)
    head_switch_active: bool = False  # Is this flyer actively executing a head switch?
    head_switch_desc: str = ""  # Description of gaze target and biomechanical cues
    gaze_target: Optional[str] = None  # Slot being cross-referenced ("Point", "OC", "IC", "Tail")
    left_grip: Optional[str] = None   # What left hand grips (e.g. "Point Right Wrist")
    right_grip: Optional[str] = None  # What right hand grips
    grippers_presented: List[str] = field(default_factory=list)  # Grippers offered to teammates


@dataclass
class SlotDetail:
    """Detailed slot-specific execution guide."""
    slot_name: str         # "Point", "Outside Center", "Inside Center", "Tail", "Videographer"
    color: str             # Hex color code
    role_summary: str      # 1-line role
    duties_description: str  # Step-by-step duties
    grip_actions: str      # Grips taken and presented
    head_switch_notes: str # Biomechanical head switch instructions
    rotation_degrees: str  # Degree of turn/translation
    key_role: str          # Role in keying


@dataclass
class FormationDefinition:
    """Complete specification for a random or block formation."""
    code: str              # "A", "B", ... or "1", "2", ... "22"
    name: str              # "Unipod", "Molar - Molar", etc.
    is_block: bool         # False = Random (1 pt), True = Block (2 pts)
    points: int            # 1 or 2
    initial_name: str      # Name of initial formation
    second_name: Optional[str] = None  # Name of closing formation (for blocks)
    supports_vertical: bool = False    # Supports Over/Under vertical technique
    subgroup_split: str = ""  # "2-way / 2-way", "Solo / 3-way", etc.
    inter_degrees: str = ""   # Rotation degrees for subgroups
    primary_key_slot: str = "Inside Center"  # Who keys
    key_trigger: str = ""     # What triggers key
    key_method: str = "Visual Nod / Flash"  # Method of key
    shared_key_notes: str = "" # Secondary key rules
    head_switch_summary: str = "" # Summary of head switches in this formation
    coach_tips: List[str] = field(default_factory=list)
    pitfalls_and_busts: List[str] = field(default_factory=list)
    
    # 3D States:
    state_initial: Dict[str, Flyer3DState] = field(default_factory=dict)
    state_inter: Optional[Dict[str, Flyer3DState]] = None
    state_close: Optional[Dict[str, Flyer3DState]] = None
    
    # Optional vertical alternate states
    state_inter_vertical: Optional[Dict[str, Flyer3DState]] = None
    state_close_vertical: Optional[Dict[str, Flyer3DState]] = None
    
    # Slot Details (Point, OC, IC, Tail, Videographer)
    slot_details: Dict[str, SlotDetail] = field(default_factory=dict)


# Standard SDC Rhythm XP Colors (as shown in Continuity Booklet)
COLOR_POINT = "#EF4444"    # Red (Point)
COLOR_OC = "#10B981"       # Green (Outside Center)
COLOR_IC = "#3B82F6"       # Blue (Inside Center)
COLOR_TAIL = "#EAB308"     # Yellow (Tail)
COLOR_VIDEO = "#A855F7"    # Purple (Videographer)


def _build_dive_pool() -> Dict[str, FormationDefinition]:
    pool: Dict[str, FormationDefinition] = {}

    # =========================================================================
    # 16 RANDOMS (A through Q, including J)
    # =========================================================================

    # RANDOM A: UNIPOD
    pool["A"] = FormationDefinition(
        code="A", name="Unipod", is_block=False, points=1,
        initial_name="Unipod",
        subgroup_split="No split (Random)",
        primary_key_slot="Inside Center",
        key_trigger="When Outside Center and Inside Center secure Point's wrists and Tail closes",
        key_method="Sharp chin nod / flash",
        shared_key_notes="If Inside Center view is obstructed, Tail gives shared eye-contact key",
        head_switch_summary="Point head switches forward/down to maintain heading. Centers reference Point. Tail cross-references Point.",
        coach_tips=[
            "Point must present steady, symmetrical wrist grippers without reaching back.",
            "Centers must not pull Point backward; fly your own bodies into the slot.",
            "Tail anchors the rear base and references the Point-Tail axis."
        ],
        pitfalls_and_busts=[
            "Point reaching back with straight arms (dumps air from chest, drops fall rate).",
            "Inside Center keying before Outside Center has a secure grip.",
            "Tail sliding off the central axis, creating an asymmetric chevron."
        ],
        state_initial={
            "Point": Flyer3DState(0, 55, 0, 0, head_turn_deg=0, grippers_presented=["Left Wrist", "Right Wrist"]),
            "OC": Flyer3DState(-35, 10, 0, 45, head_turn_deg=-20, gaze_target="Point", right_grip="Point Left Wrist"),
            "IC": Flyer3DState(35, 10, 0, 315, head_turn_deg=20, gaze_target="Point", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(0, -50, 0, 180, head_turn_deg=0, gaze_target="Point", left_grip="OC Left Ankle", right_grip="IC Right Ankle")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Wing / Outfacing Anchor",
                                "Fly to front apex; present level wrists into clean air; hold heading 0°.",
                                "Presents Left and Right Wrists. Takes no grips.",
                                "Head held high; look at horizon; do not look down or back at centers.",
                                "0° In-Place", "Waits for key; launches into next move instantly"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Center Hub",
                             "Fly to left shoulder of Point; take Point's left wrist; set 45° angle.",
                             "Right hand takes Point's Left Wrist. Presents rear ankles/hips to Tail.",
                             "Head turned 20° toward Point's wrist and cross-references IC across center.",
                             "Angle setup", "Confirms grip to IC with eye contact"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Center Hub & Keyer",
                             "Fly to right shoulder of Point; take Point's right wrist; verify complete formation.",
                             "Left hand takes Point's Right Wrist. Presents left side to Tail.",
                             "Head turned toward Point and checks OC's hand closure with peripheral vision.",
                             "Angle setup", "PRIMARY KEY: Delivers sharp chin nod the instant all grips touch"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Anchor & Base",
                               "Fly up to close rear; take OC and IC ankles/legs; balance the Point-Tail axis.",
                               "Takes OC and IC rear grippers.",
                               "Head switch upward across formation to lock eyes on Point for planar trim.",
                               "0° Drive forward", "Reacts explosively to IC's key")
        }
    )

    # RANDOM B: STAIRSTEP DIAMOND
    pool["B"] = FormationDefinition(
        code="B", name="Stairstep Diamond", is_block=False, points=1,
        initial_name="Stairstep Diamond",
        subgroup_split="No split (Random)",
        primary_key_slot="Inside Center",
        key_trigger="All 4 flyers locked in staggered diamond with correct offset",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Point and Tail clone cross-reference each other to set offset angle and planar levels.",
        coach_tips=[
            "Maintain the stairstep offset without collapsing into a flat diamond.",
            "Centers set the middle width; wings must not pinch in.",
            "Use clone cross-referencing between Point and Tail to gauge true team level."
        ],
        pitfalls_and_busts=[
            "Pinching the diamond too tight, causing knee clashes.",
            "Level step-off: IC floating above OC, causing formation tilt."
        ],
        state_initial={
            "Point": Flyer3DState(-25, 60, 0, 20, head_turn_deg=-20, gaze_target="Tail", left_grip="OC Left Wrist"),
            "OC": Flyer3DState(-45, 10, 0, 70, head_turn_deg=20, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(25, -10, 0, 250, head_turn_deg=20, gaze_target="OC", left_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(45, -60, 0, 200, head_turn_deg=-20, gaze_target="Point", right_grip="Point Left Ankle")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Forward Stagger Apex", "Hold upper left diamond point; maintain 20° heading.", "Takes OC wrist; presents ankle.", "References Tail across the diagonal.", "Offset slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Lateral Link", "Bridge Point and IC; lock arm-to-wrist grip.", "Takes IC wrist; presents wrist to Point.", "Looks inward toward IC.", "Lateral trim", "Assists key confirmation"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Lateral Link & Keyer", "Hold center offset; take Tail wrist; scan whole formation.", "Takes Tail wrist; presents wrist to OC.", "Cross-references OC and checks Point.", "Center anchor", "PRIMARY KEY: Keys upon grip lock"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Stagger Apex", "Hold rear right diamond point; balance fall rate.", "Takes Point ankle; presents wrist to IC.", "Locks gaze with Point across center.", "Offset drive", "Explosive release")
        }
    )

    # RANDOM C: MURPHY FLAKE
    pool["C"] = FormationDefinition(
        code="C", name="Murphy Flake", is_block=False, points=1,
        initial_name="Murphy Flake",
        primary_key_slot="Inside Center",
        key_trigger="Flake line established with alternating hand-to-wrist connections",
        key_method="Visual nod",
        head_switch_summary="All flyers look across formation. Centers keep shoulders square while checking wings.",
        coach_tips=[
            "Maintain wide planar spacing; avoid accordion folding.",
            "Flyers must fly their own bodies into position before taking grips."
        ],
        pitfalls_and_busts=["Snatching wrists from too far away, causing the line to curve or potato-chip."],
        state_initial={
            "Point": Flyer3DState(-60, 40, 0, 60, head_turn_deg=0, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-20, 15, 0, 30, head_turn_deg=-30, gaze_target="Point", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(20, -15, 0, 210, head_turn_deg=30, gaze_target="Tail", right_grip="OC Right Wrist"),
            "Tail": Flyer3DState(60, -40, 0, 240, head_turn_deg=0, gaze_target="IC", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Outer Flake Wing", "Fly outer left perimeter; maintain flake heading.", "Takes OC wrist.", "Looks inward at OC.", "Perimeter slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Flake Link", "Connect Point with center; match fall rate.", "Takes IC wrist; presents wrist to Point.", "Checks Point and IC simultaneously.", "Planar trim", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Flake Anchor & Keyer", "Anchor middle flake; verify grips across line.", "Takes OC wrist; presents wrist to Tail.", "Looks across flake to verify both wings.", "Central anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Outer Flake Wing", "Fly outer right perimeter; anchor the rear.", "Takes IC wrist.", "Looks inward at IC.", "Perimeter drive", "Reacts on key")
        }
    )

    # RANDOM D: YUAN
    pool["D"] = FormationDefinition(
        code="D", name="Yuan", is_block=False, points=1,
        initial_name="Yuan",
        primary_key_slot="Inside Center",
        key_trigger="Asymmetrical grips locked on ankles and wrists",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Point head switches to present ankle; IC monitors Point's leg grip.",
        coach_tips=["Asymmetric geometry requires IC to hold a rock-steady fall rate while Point presents."],
        pitfalls_and_busts=["Point swinging legs out of reach; Centers over-reaching."],
        state_initial={
            "Point": Flyer3DState(-40, 45, 0, 90, head_turn_deg=45, gaze_target="OC", grippers_presented=["Left Ankle"]),
            "OC": Flyer3DState(-10, 10, 0, 45, head_turn_deg=-20, gaze_target="Point", right_grip="Point Left Ankle"),
            "IC": Flyer3DState(25, -10, 0, 225, head_turn_deg=30, gaze_target="Tail", left_grip="OC Left Wrist"),
            "Tail": Flyer3DState(55, -45, 0, 270, head_turn_deg=-30, gaze_target="IC", right_grip="IC Right Ankle")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Asymmetric Wing", "Turn 90°; present leg clean into OC space.", "Presents Left Ankle.", "Head switch right to verify OC grip.", "90° Turn", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Forward Link", "Catch Point's ankle gently; do not pull.", "Takes Point Ankle; presents wrist.", "Looks down at Point ankle.", "Forward step", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Pivot & Keyer", "Hold center base; connect OC and Tail.", "Takes OC wrist; presents ankle.", "Scans Point and Tail.", "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Wing", "Take IC ankle; stabilize rear quadrant.", "Takes IC Ankle.", "Looks inward at IC.", "Rear drive", "Reacts on key")
        }
    )

    # RANDOM E: MEEKER
    pool["E"] = FormationDefinition(
        code="E", name="Meeker", is_block=False, points=1,
        initial_name="Meeker",
        primary_key_slot="Inside Center",
        key_trigger="Compact compressed center built with wings in position",
        key_method="Visual nod",
        head_switch_summary="Centers lock eyes in tight compression. Wings cross-reference across center.",
        coach_tips=["Centers must compress tight; wings stay wide enough not to funnel the center."],
        pitfalls_and_busts=["Centers pushing away from each other; wings lagging behind."],
        state_initial={
            "Point": Flyer3DState(0, 50, 0, 0, head_turn_deg=0, gaze_target="Tail", left_grip="OC Right Wrist"),
            "OC": Flyer3DState(-25, 0, 0, 90, head_turn_deg=0, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(25, 0, 0, 270, head_turn_deg=0, gaze_target="OC", left_grip="OC Right Wrist"),
            "Tail": Flyer3DState(0, -50, 0, 180, head_turn_deg=0, gaze_target="Point", right_grip="IC Left Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Apex", "Fly to front apex; take OC wrist.", "Takes OC wrist.", "Looks down through center at Tail.", "Forward slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Center Compression", "Face IC directly; lock tight center.", "Takes IC wrist; presents to Point.", "Direct eye contact with IC.", "Center compression", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Center Compression & Keyer", "Face OC directly; verify both wing grips.", "Takes OC wrist; presents to Tail.", "Direct eye contact with OC; peripheral on wings.", "Center compression", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Apex", "Fly to rear apex; take IC wrist.", "Takes IC wrist.", "Looks up through center at Point.", "Rear drive", "Reacts on key")
        }
    )

    # RANDOM F: OPEN ACCORDION
    pool["F"] = FormationDefinition(
        code="F", name="Open Accordion", is_block=False, points=1,
        initial_name="Open Accordion",
        primary_key_slot="Inside Center",
        key_trigger="Zig-zag line complete with equal spacing across all 4 flyers",
        key_method="Visual nod",
        head_switch_summary="Strict clone cross-referencing: Point references Tail; OC references IC.",
        coach_tips=[
            "Do not let the accordion compress into a straight line.",
            "Cross-reference your clone to match angles and levels exactly."
        ],
        pitfalls_and_busts=["Folding into a ball; level discrepancy between outer flyers."],
        state_initial={
            "Point": Flyer3DState(-50, 45, 0, 45, head_turn_deg=10, gaze_target="Tail", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-15, 15, 0, 225, head_turn_deg=-10, gaze_target="IC", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(15, -15, 0, 45, head_turn_deg=10, gaze_target="OC", right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(50, -45, 0, 225, head_turn_deg=-10, gaze_target="Point", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Outer Accordion Wing", "Hold 45° heading; grip OC wrist.", "Takes OC wrist.", "Cross-references Tail on opposite end.", "Radial slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Accordion Link", "Hold 225° heading; connect Point and IC.", "Takes IC wrist; presents to Point.", "Looks at IC.", "Angle maintenance", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Accordion Link & Keyer", "Hold 45° heading; connect OC and Tail.", "Takes Tail wrist; presents to OC.", "Looks across at OC; verifies wings.", "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Outer Accordion Wing", "Hold 225° heading; grip IC wrist.", "Takes IC wrist.", "Cross-references Point across line.", "Radial drive", "Reacts on key")
        }
    )

    # RANDOM G: CATACCORD
    pool["G"] = FormationDefinition(
        code="G", name="Cataccord", is_block=False, points=1,
        initial_name="Cataccord",
        primary_key_slot="Inside Center",
        key_trigger="Tail secures double leg grips on IC and OC while Point closes accordion",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Tail looks down at legs to ensure clean cat grips; Point references centers.",
        coach_tips=["Tail must not pull backward on centers' legs; fly your chest forward into the cat."],
        pitfalls_and_busts=["Tail pulling centers apart; Point over-sliding."],
        state_initial={
            "Point": Flyer3DState(0, 55, 0, 0, head_turn_deg=0, gaze_target="IC", left_grip="OC Right Wrist"),
            "OC": Flyer3DState(-30, 15, 0, 90, head_turn_deg=-30, gaze_target="Point", right_grip="Point Left Wrist"),
            "IC": Flyer3DState(30, 15, 0, 270, head_turn_deg=30, gaze_target="Point", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(0, -35, 0, 0, head_turn_deg=0, gaze_target="IC", left_grip="OC Left Ankle", right_grip="IC Right Ankle")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Accordion Apex", "Present/take with centers in accordion.", "Takes OC wrist.", "Looks at centers.", "Front setup", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Cat Front", "Hold steady leg presentation for Tail.", "Presents ankle to Tail.", "Looks at Point.", "Leg presentation", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Cat Front & Keyer", "Hold steady leg presentation; verify Tail grips.", "Presents ankle to Tail.", "Peripheral check on Tail.", "Center keyer", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Cat Flyer (Double Leg Grips)", "Drive in infacing; take both centers' ankles.", "Takes OC & IC ankles.", "Looks at centers' hips.", "Cat drive", "Reacts on key")
        }
    )

    # RANDOM H: BOW
    pool["H"] = FormationDefinition(
        code="H", name="Bow", is_block=False, points=1,
        initial_name="Bow",
        primary_key_slot="Inside Center",
        key_trigger="Classic bow configuration built with interlocking center grips",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Centers face diagonally; wings look inward at center intersection.",
        coach_tips=["Standard exit formation. Keep it compact; wings must stay close to centers."],
        pitfalls_and_busts=["Centers blowing apart on exit; wings funneling the center."],
        state_initial={
            "Point": Flyer3DState(-45, 45, 0, 45, head_turn_deg=0, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-15, 0, 0, 315, head_turn_deg=45, gaze_target="IC", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(15, 0, 0, 135, head_turn_deg=-45, gaze_target="OC", right_grip="OC Right Wrist"),
            "Tail": Flyer3DState(45, -45, 0, 225, head_turn_deg=0, gaze_target="IC", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Bow Wing", "Launch exit; grip OC wrist.", "Takes OC wrist.", "Looks inward at OC.", "Bow wing", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Outside Bow Center", "Float exit; lock center bow with IC.", "Takes IC wrist.", "Looks at IC.", "Center exit", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Inside Bow Center & Keyer", "Sneak low on exit; lock bow with OC.", "Takes OC wrist.", "Looks at OC.", "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Bow Wing", "Drop exit; grip IC wrist.", "Takes IC wrist.", "Looks inward at IC.", "Bow tail", "Reacts on key")
        }
    )

    # RANDOM I: SATELLITE (OPEN STAR)
    pool["I"] = FormationDefinition(
        code="I", name="Satellite", is_block=False, points=1,
        initial_name="Satellite",
        primary_key_slot="Inside Center",
        key_trigger="All 4 radial grips secure; formation round and level",
        key_method="Visual nod",
        head_switch_summary="All 4 flyers face tangentially/outward; head switch inward to verify grips.",
        coach_tips=["High fall-rate sensitivity. Keep arch flat and quiet."],
        pitfalls_and_busts=["Flyers turning too far out and losing sight of grips."],
        state_initial={
            "Point": Flyer3DState(0, 45, 0, 90, head_turn_deg=-45, gaze_target="OC", left_grip="OC Right Wrist"),
            "OC": Flyer3DState(-45, 0, 0, 180, head_turn_deg=-45, gaze_target="Tail", left_grip="Tail Right Wrist"),
            "IC": Flyer3DState(45, 0, 0, 0, head_turn_deg=-45, gaze_target="Point", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(0, -45, 0, 270, head_turn_deg=-45, gaze_target="IC", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Radial Wing", "Hold 90° heading; take OC wrist.", "Takes OC wrist.", "Head turned left into center.", "Radial spin", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Radial Center", "Hold 180° heading; take Tail wrist.", "Takes Tail wrist.", "Head turned left into center.", "Radial spin", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Radial Center & Keyer", "Hold 0° heading; take Point wrist.", "Takes Point wrist.", "Head turned left into center.", "Radial spin", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Radial Wing", "Hold 270° heading; take IC wrist.", "Takes IC wrist.", "Head turned left into center.", "Radial spin", "Reacts on key")
        }
    )

    # RANDOM J: DONUT
    pool["J"] = FormationDefinition(
        code="J", name="Donut", is_block=False, points=1,
        initial_name="Donut",
        primary_key_slot="Inside Center",
        key_trigger="Closed donut ring with alternating wrist/arm grips",
        key_method="Visual nod from Inside Center",
        head_switch_summary="All flyers look across center of circle at diagonal clone.",
        coach_tips=["Maintain circular quadrant symmetry. Do not allow donut to flatten."],
        pitfalls_and_busts=["Unequal circle diameter; one side collapsing inward."],
        state_initial={
            "Point": Flyer3DState(-25, 35, 0, 45, head_turn_deg=-15, gaze_target="Tail", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-35, -25, 0, 135, head_turn_deg=-15, gaze_target="IC", right_grip="Tail Left Wrist"),
            "IC": Flyer3DState(25, 35, 0, 315, head_turn_deg=15, gaze_target="OC", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(35, -25, 0, 225, head_turn_deg=-15, gaze_target="Point", right_grip="IC Left Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Donut Quadrant 1", "Hold circle arc; take OC wrist.", "Takes OC wrist.", "Looks across at Tail.", "Circular arc", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Donut Quadrant 2", "Hold circle arc; take Tail wrist.", "Takes Tail wrist.", "Looks across at IC.", "Circular arc", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Donut Quadrant 3 & Keyer", "Hold circle arc; take Point wrist.", "Takes Point wrist.", "Looks across at OC.", "Circular arc", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Donut Quadrant 4", "Hold circle arc; take IC wrist.", "Takes IC wrist.", "Looks across at Point.", "Circular arc", "Reacts on key")
        }
    )

    # RANDOM K: HOOK
    pool["K"] = FormationDefinition(
        code="K", name="Hook", is_block=False, points=1,
        initial_name="Hook",
        primary_key_slot="Inside Center",
        key_trigger="Offset hook shape with hand-to-leg grips locked",
        key_method="Visual nod",
        head_switch_summary="Flyers taking leg grips head switch down/back to confirm leg position.",
        coach_tips=["Leg grippers must be presented firmly; takers fly to the leg rather than pulling."],
        pitfalls_and_busts=["Kicking legs away; pulling taker off heading."],
        state_initial={
            "Point": Flyer3DState(-30, 50, 0, 0, head_turn_deg=30, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(10, 20, 0, 0, head_turn_deg=-20, gaze_target="Point", left_grip="IC Right Ankle"),
            "IC": Flyer3DState(35, -20, 0, 180, head_turn_deg=-30, gaze_target="Tail", left_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(-10, -50, 0, 180, head_turn_deg=20, gaze_target="IC", right_grip="Point Left Ankle")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Hook Front", "Hold 0° heading; take OC wrist.", "Takes OC wrist.", "Looks at OC.", "Front hook", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Hook Center", "Take IC ankle with left hand.", "Takes IC ankle.", "Looks down at IC ankle.", "Center hook", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Hook Center & Keyer", "Present ankle to OC; take Tail wrist.", "Takes Tail wrist.", "Looks at Tail.", "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Hook Rear", "Take Point ankle; hold 180°.", "Takes Point ankle.", "Looks up at Point ankle.", "Rear hook", "Reacts on key")
        }
    )

    # RANDOM L: ADDER
    pool["L"] = FormationDefinition(
        code="L", name="Adder", is_block=False, points=1,
        initial_name="Adder",
        primary_key_slot="Inside Center",
        key_trigger="Stepped zig-zag complete along the Point-Tail axis",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Point and Tail lock on central line; Centers reference each other.",
        coach_tips=["Strict adherence to the Magic Point-Tail line; keep centers compact."],
        pitfalls_and_busts=["Centers sliding wide, stretching wings into reaching."],
        state_initial={
            "Point": Flyer3DState(0, 60, 0, 0, head_turn_deg=0, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-25, 20, 0, 180, head_turn_deg=30, gaze_target="IC", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(25, -20, 0, 0, head_turn_deg=-30, gaze_target="OC", right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(0, -60, 0, 180, head_turn_deg=0, gaze_target="IC", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Adder Front", "Stay on Point-Tail axis; take OC wrist.", "Takes OC wrist.", "Looks at OC.", "Axis anchor", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Adder Left Center", "Inface rearward; connect Point and IC.", "Takes IC wrist.", "Looks across at IC.", "Center link", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Adder Right Center & Keyer", "Inface forward; connect OC and Tail.", "Takes Tail wrist.", "Looks across at OC.", "Center link", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Adder Rear", "Stay on Point-Tail axis; take IC wrist.", "Takes IC wrist.", "Looks at IC.", "Axis anchor", "Reacts on key")
        }
    )

    # RANDOM M: STAR
    pool["M"] = FormationDefinition(
        code="M", name="Star", is_block=False, points=1,
        initial_name="Star",
        primary_key_slot="Inside Center",
        key_trigger="Pure round 4-way star; all 4 wrist grips connected simultaneously",
        key_method="Visual nod / simultaneous flash",
        head_switch_summary="Every flyer faces directly into centerpoint (0,0); direct eye contact with diagonal partner.",
        coach_tips=[
            "The baseline formation of 4-way skydiving. Tests pure quadrant discipline.",
            "All 4 flyers must have identical fall rates and level planes.",
            "Key should be instantaneous upon 4th grip touch."
        ],
        pitfalls_and_busts=[
            "Pushing into the star (causes popcorn explosion).",
            "Pulling out of the star (causes oval elongation).",
            "Lazy grip release (busted separation)."
        ],
        state_initial={
            "Point": Flyer3DState(0, 42, 0, 180, head_turn_deg=0, gaze_target="Tail", left_grip="OC Right Wrist", right_grip="IC Left Wrist"),
            "OC": Flyer3DState(-42, 0, 0, 90, head_turn_deg=0, gaze_target="IC", left_grip="Tail Right Wrist", right_grip="Point Left Wrist"),
            "IC": Flyer3DState(42, 0, 0, 270, head_turn_deg=0, gaze_target="OC", left_grip="Point Right Wrist", right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(0, -42, 0, 0, head_turn_deg=0, gaze_target="Point", left_grip="IC Right Wrist", right_grip="OC Left Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "North Star Arm", "Fly directly South to (0, 42); take OC and IC wrists.", "Takes OC & IC wrists.", "Locks eyes with Tail across center.", "Radial in-place", "Simultaneous flash release"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "West Star Arm", "Fly directly East to (-42, 0); take Point and Tail wrists.", "Takes Point & Tail wrists.", "Locks eyes with IC across center.", "Radial in-place", "Simultaneous flash release"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "East Star Arm & Keyer", "Fly directly West to (42, 0); take Point and Tail wrists.", "Takes Point & Tail wrists.", "Locks eyes with OC across center.", "Radial in-place", "PRIMARY KEY: Keys on 4th grip touch"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "South Star Arm", "Fly directly North to (0, -42); take OC and IC wrists.", "Takes OC & IC wrists.", "Locks eyes with Point across center.", "Radial in-place", "Simultaneous flash release")
        }
    )

    # RANDOM N: CRANK
    pool["N"] = FormationDefinition(
        code="N", name="Crank", is_block=False, points=1,
        initial_name="Crank",
        primary_key_slot="Inside Center",
        key_trigger="Offset rectangular box grips established without torquing",
        key_method="Visual nod",
        head_switch_summary="Centers reference each other; wings look along grip line.",
        coach_tips=["High rotational torque potential. Maintain quiet air; do not twist grips."],
        pitfalls_and_busts=["Torquing the box into a spin; level discrepancies."],
        state_initial={
            "Point": Flyer3DState(-25, 45, 0, 90, head_turn_deg=30, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-35, -15, 0, 0, head_turn_deg=-30, gaze_target="Tail", left_grip="Tail Left Wrist"),
            "IC": Flyer3DState(35, 15, 0, 180, head_turn_deg=-30, gaze_target="Point", left_grip="Point Left Wrist"),
            "Tail": Flyer3DState(25, -45, 0, 270, head_turn_deg=30, gaze_target="IC", right_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Crank Wing", "Hold 90° heading; take OC wrist.", "Takes OC wrist.", "Looks at OC.", "Offset box", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Crank Center", "Hold 0° heading; take Tail wrist.", "Takes Tail wrist.", "Looks at Tail.", "Offset box", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Crank Center & Keyer", "Hold 180° heading; take Point wrist.", "Takes Point wrist.", "Looks at Point.", "Offset box", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Crank Wing", "Hold 270° heading; take IC wrist.", "Takes IC wrist.", "Looks at IC.", "Offset box", "Reacts on key")
        }
    )

    # RANDOM O: SATELLITE (OPPOSED)
    pool["O"] = FormationDefinition(
        code="O", name="Satellite", is_block=False, points=1,
        initial_name="Satellite",
        primary_key_slot="Inside Center",
        key_trigger="Opposed satellite ring complete; level across all flyers",
        key_method="Visual nod",
        head_switch_summary="All flyers check diagonal clone for level matching.",
        coach_tips=["Clone cross-referencing is critical for stability."],
        pitfalls_and_busts=["Over-rotation; dropping outside elbows."],
        state_initial={
            "Point": Flyer3DState(-35, 35, 0, 315, head_turn_deg=20, gaze_target="Tail", right_grip="IC Left Wrist"),
            "OC": Flyer3DState(-35, -35, 0, 225, head_turn_deg=20, gaze_target="IC", left_grip="Point Left Wrist"),
            "IC": Flyer3DState(35, 35, 0, 45, head_turn_deg=-20, gaze_target="OC", left_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(35, -35, 0, 135, head_turn_deg=20, gaze_target="Point", right_grip="OC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Opposed Satellite Arm", "Hold 315°; take IC wrist.", "Takes IC wrist.", "Looks at Tail.", "Opposed arc", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Opposed Satellite Arm", "Hold 225°; take Point wrist.", "Takes Point wrist.", "Looks at IC.", "Opposed arc", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Opposed Satellite Arm & Keyer", "Hold 45°; take Tail wrist.", "Takes Tail wrist.", "Looks at OC.", "Opposed arc", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Opposed Satellite Arm", "Hold 135°; take OC wrist.", "Takes OC wrist.", "Looks at Point.", "Opposed arc", "Reacts on key")
        }
    )

    # RANDOM P: SIDEBODY
    pool["P"] = FormationDefinition(
        code="P", name="Sidebody", is_block=False, points=1,
        initial_name="Sidebody",
        primary_key_slot="Inside Center",
        key_trigger="All sidebody grips locked (hand-to-hip/wrist); parallel headings",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Centers look at each other; Point references Tail down the flank.",
        coach_tips=[
            "Standard exit formation from Twin Otter. Maintain close flank proximity.",
            "Flyers must fly side-by-side with zero yaw angle divergence."
        ],
        pitfalls_and_busts=["Blowing apart laterally; one flyer banking away."],
        state_initial={
            "Point": Flyer3DState(-35, 45, 0, 0, head_turn_deg=45, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-15, 0, 0, 0, head_turn_deg=90, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(15, 0, 0, 0, head_turn_deg=-90, gaze_target="OC", left_grip="OC Right Wrist"),
            "Tail": Flyer3DState(35, -45, 0, 0, head_turn_deg=-45, gaze_target="IC", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Flank", "Hold 0° heading; lock right hand to OC wrist.", "Takes OC wrist.", "Head turned 45° right to OC.", "Flank alignment", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Left Flank", "Hold 0° heading; lock right hand to IC wrist.", "Takes IC wrist.", "Direct eye contact with IC.", "Center alignment", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Right Flank & Keyer", "Hold 0° heading; lock left hand to OC wrist.", "Takes OC wrist.", "Direct eye contact with OC.", "Center alignment", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Flank", "Hold 0° heading; lock left hand to IC wrist.", "Takes IC wrist.", "Head turned 45° left to IC.", "Flank alignment", "Reacts on key")
        }
    )

    # RANDOM Q: PHALANX
    pool["Q"] = FormationDefinition(
        code="Q", name="Phalanx", is_block=False, points=1,
        initial_name="Phalanx",
        primary_key_slot="Inside Center",
        key_trigger="All 4 flyers aligned side-by-side in a straight horizontal line",
        key_method="Visual nod from Inside Center",
        head_switch_summary="All flyers look across the line; outer wings clone cross-reference each other.",
        coach_tips=["Strict level matching across all 4 flyers; avoid bowing the phalanx."],
        pitfalls_and_busts=["Outer wings lagging behind or folding forward into a horseshoe."],
        state_initial={
            "Point": Flyer3DState(-60, 0, 0, 0, head_turn_deg=60, gaze_target="Tail", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-20, 0, 0, 0, head_turn_deg=45, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(20, 0, 0, 0, head_turn_deg=-45, gaze_target="OC", left_grip="OC Right Wrist"),
            "Tail": Flyer3DState(60, 0, 0, 0, head_turn_deg=-60, gaze_target="Point", left_grip="IC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Left End Phalanx", "Align in line; match OC fall rate exactly.", "Takes OC wrist.", "Looks down line across to Tail.", "Line alignment", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Left Phalanx", "Maintain center line spacing.", "Takes IC wrist; presents to Point.", "Looks at IC and Point.", "Line alignment", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Right Phalanx & Keyer", "Anchor phalanx line; verify wings.", "Takes OC wrist; presents to Tail.", "Looks at OC and Tail.", "Line anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Right End Phalanx", "Align in line; match IC fall rate exactly.", "Takes IC wrist.", "Looks down line across to Point.", "Line alignment", "Reacts on key")
        }
    )

    # =========================================================================
    # 22 BLOCKS (1 through 22)
    # =========================================================================

    # BLOCK 1: MOLAR - MOLAR
    pool["1"] = FormationDefinition(
        code="1", name="Molar - Molar", is_block=True, points=2,
        initial_name="Molar", second_name="Molar",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Front 360° / Rear 360° (or 270°/90°)",
        primary_key_slot="Inside Center",
        key_trigger="Build 1: Molar built solid -> Key -> Break -> Inter -> Close Molar",
        key_method="Visual nod from Inside Center on Build 1; simultaneous closure on Build 2",
        head_switch_summary="During inter: Point head switches right to track IC; IC head switches left to track OC piece.",
        coach_tips=[
            "Vertical Technique: Front piece (Point + OC) generates slight lift to go over rear piece.",
            "Rear piece (IC + Tail) stays flat or slightly under in clean air.",
            "Piece partners must maintain firm, locked grip throughout the 360° rotation."
        ],
        pitfalls_and_busts=["Piece partners breaking grip during inter rotation; front piece funneling into rear piece burble."],
        state_initial={
            "Point": Flyer3DState(-25, 40, 0, 45, head_turn_deg=0, right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-40, 10, 0, 45, head_turn_deg=0, left_grip="Point Right Wrist"),
            "IC": Flyer3DState(25, -10, 0, 225, head_turn_deg=0, right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(40, -40, 0, 225, head_turn_deg=0, left_grip="IC Right Wrist")
        },
        state_inter={
            "Point": Flyer3DState(30, 40, 0, 225, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Head switch left to track rear piece", gaze_target="IC"),
            "OC": Flyer3DState(10, 15, 0, 225, head_turn_deg=-30, gaze_target="Tail"),
            "IC": Flyer3DState(-10, -15, 0, 45, head_turn_deg=30, head_switch_active=True, head_switch_desc="Head switch right to track front piece", gaze_target="OC"),
            "Tail": Flyer3DState(-30, -40, 0, 45, head_turn_deg=45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(25, -40, 0, 225, head_turn_deg=0, right_grip="OC Left Wrist"),
            "OC": Flyer3DState(40, -10, 0, 225, head_turn_deg=0, left_grip="Point Right Wrist"),
            "IC": Flyer3DState(-25, 10, 0, 45, head_turn_deg=0, right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(-40, 40, 0, 45, head_turn_deg=0, left_grip="IC Right Wrist")
        },
        state_inter_vertical={
            "Point": Flyer3DState(20, 30, 15, 225, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Flying over rear piece; head switches down", gaze_target="IC"),
            "OC": Flyer3DState(5, 10, 15, 225, head_turn_deg=-30, gaze_target="Tail"),
            "IC": Flyer3DState(-5, -10, -15, 45, head_turn_deg=30, head_switch_active=True, head_switch_desc="Flying under front piece; head switches up", gaze_target="OC"),
            "Tail": Flyer3DState(-20, -30, -15, 45, head_turn_deg=45, gaze_target="Point")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Piece Outside Flyer", "Spin 2-way with OC 360°; fly over in vertical.", "Locks grip with OC.", "Head switch to spot rear piece at 180° inter.", "360° Piece Spin", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Front Piece Inside Pivot", "Control piece radius; match Point fall rate.", "Locks grip with Point.", "Maintains focus on Point.", "360° Piece Spin", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Rear Piece Inside Pivot & Keyer", "Key Build 1; rotate rear piece 360° with Tail.", "Locks grip with Tail.", "Head switch left to spot closing front piece.", "360° Piece Spin", "PRIMARY KEY Build 1"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Piece Outside Flyer", "Drive rear piece rotation with strong legs.", "Locks grip with IC.", "Focus on IC and closing target.", "360° Piece Spin", "Assists close")
        }
    )

    # BLOCK 2: SIDEBODY DONUT - SIDEFLAKE DONUT
    pool["2"] = FormationDefinition(
        code="2", name="Sidebody Donut - Sideflake Donut", is_block=True, points=2,
        initial_name="Sidebody Donut", second_name="Sideflake Donut",
        subgroup_split="3-Way (OC + IC + Tail) / Solo (Point)",
        inter_degrees="3-Way 360° Spin / Solo Translation",
        primary_key_slot="Point",
        key_trigger="Sidebody Donut locked -> Point keys -> 3-Way turns 360° while Point translates -> Rebuild Sideflake Donut",
        head_switch_summary="Point cross-references 3-way center during translation; 3-way maintains tight donut axis throughout 360° turn.",
        coach_tips=[
            "Point must release cleanly and translate down the line without drifting wide.",
            "3-way must turn smoothly as a rigid unit without deforming the donut shape."
        ],
        pitfalls_and_busts=[
            "3-way funneling or expanding radius during 360° spin.",
            "Point arriving late at closing sideflake."
        ],
        state_initial={
            "Point": Flyer3DState(0, 36, 0, 180, head_turn_deg=0),
            "OC": Flyer3DState(0, 10, 0, 90, head_turn_deg=0),
            "IC": Flyer3DState(16, -20, 0, 45, head_turn_deg=0),
            "Tail": Flyer3DState(-16, -20, 0, 315, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(22, 12, 0, 180, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Spotting 3-way center", gaze_target="OC"),
            "OC": Flyer3DState(-5, -5, 0, 270, head_turn_deg=0, gaze_target="Point"),
            "IC": Flyer3DState(-18, 12, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(15, -12, 0, 135, head_turn_deg=0)
        },
        state_close={
            "Point": Flyer3DState(15, -10, 0, 0, head_turn_deg=-20),
            "OC": Flyer3DState(0, -10, 0, 0, head_turn_deg=0),
            "IC": Flyer3DState(-18, -25, 0, 45, head_turn_deg=0),
            "Tail": Flyer3DState(-20, 8, 0, 135, head_turn_deg=0)
        }
    )

    # BLOCK 3: SIDEFLAKE OPAL - TURF
    pool["3"] = FormationDefinition(
        code="3", name="Sideflake Opal - Turf", is_block=True, points=2,
        initial_name="Sideflake Opal", second_name="Turf",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Translation + 180° rotation",
        primary_key_slot="Inside Center",
        key_trigger="Sideflake Opal complete -> Key -> Cross center -> Turf",
        head_switch_summary="Both centers head switch across center to monitor crossing paths.",
        coach_tips=["Crossover requires strict Start-Coast-Stop momentum management."],
        pitfalls_and_busts=["Collision during center crossover; overshooting the Turf build."],
        state_initial={
            "Point": Flyer3DState(-40, 35, 0, 60, head_turn_deg=0),
            "OC": Flyer3DState(-15, 10, 0, 60, head_turn_deg=0),
            "IC": Flyer3DState(15, -10, 0, 240, head_turn_deg=0),
            "Tail": Flyer3DState(40, -35, 0, 240, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-10, 50, 0, 150, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Tracking Tail piece", gaze_target="Tail"),
            "OC": Flyer3DState(-25, 20, 0, 150, head_turn_deg=-20, gaze_target="IC"),
            "IC": Flyer3DState(25, -20, 0, 330, head_turn_deg=20, head_switch_active=True, head_switch_desc="Tracking OC piece", gaze_target="OC"),
            "Tail": Flyer3DState(10, -50, 0, 330, head_turn_deg=30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(30, 25, 0, 240, head_turn_deg=0),
            "OC": Flyer3DState(10, -15, 0, 240, head_turn_deg=0),
            "IC": Flyer3DState(-10, 15, 0, 60, head_turn_deg=0),
            "Tail": Flyer3DState(-30, -25, 0, 60, head_turn_deg=0)
        }
    )

    # BLOCK 4: MONOPOD - MONOPOD
    pool["4"] = FormationDefinition(
        code="4", name="Monopod - Monopod", is_block=True, points=2,
        initial_name="Monopod", second_name="Monopod",
        subgroup_split="Solo (Point) + 3-Way (OC, IC, Tail)",
        inter_degrees="3-Way rotates 360°; Point rotates 360° solo",
        primary_key_slot="Inside Center",
        key_trigger="Monopod built -> Key -> 360° spins -> Rebuild Monopod",
        head_switch_summary="Point head switches to track 3-way rotation; IC monitors Point's arrival.",
        coach_tips=["Point does an isolated in-place 360° turn; 3-way rotates as a tight, unified piece."],
        pitfalls_and_busts=["Point carving wide away from the 3-way; 3-way piece breaking apart."],
        state_initial={
            "Point": Flyer3DState(0, 50, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(-30, 10, 0, 90, head_turn_deg=0),
            "IC": Flyer3DState(0, -15, 0, 180, head_turn_deg=0),
            "Tail": Flyer3DState(30, 10, 0, 270, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(0, 55, 0, 180, head_turn_deg=0, head_switch_active=True, head_switch_desc="Tracking 3-way rotation at 180° mark", gaze_target="IC"),
            "OC": Flyer3DState(15, -25, 0, 270, head_turn_deg=-30, gaze_target="Point"),
            "IC": Flyer3DState(-15, 0, 0, 0, head_turn_deg=30, head_switch_active=True, head_switch_desc="Monitoring Point", gaze_target="Point"),
            "Tail": Flyer3DState(0, 25, 0, 90, head_turn_deg=0, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(0, 50, 0, 360, head_turn_deg=0),
            "OC": Flyer3DState(-30, 10, 0, 450, head_turn_deg=0),
            "IC": Flyer3DState(0, -15, 0, 540, head_turn_deg=0),
            "Tail": Flyer3DState(30, 10, 0, 630, head_turn_deg=0)
        }
    )

    # BLOCK 5: OPAL - OPAL
    pool["5"] = FormationDefinition(
        code="5", name="Opal - Opal", is_block=True, points=2,
        initial_name="Opal", second_name="Opal",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Opposing 360° spins",
        primary_key_slot="Inside Center",
        key_trigger="Opal built solid -> Key -> 360° spins -> Rebuild Opal",
        head_switch_summary="Each piece head switches inward at 180° to calibrate closing distance.",
        coach_tips=["Vertical option allows pieces to rotate closer together without wingtips touching."],
        pitfalls_and_busts=["Pieces drifting apart during the 360° spin."],
        state_initial={
            "Point": Flyer3DState(-35, 35, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-15, 0, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(15, 0, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(35, -35, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-15, 45, 0, 225, head_turn_deg=45, head_switch_active=True, head_switch_desc="Inward head switch to IC piece", gaze_target="IC"),
            "OC": Flyer3DState(-35, 10, 0, 225, head_turn_deg=30, gaze_target="Tail"),
            "IC": Flyer3DState(35, -10, 0, 45, head_turn_deg=30, head_switch_active=True, head_switch_desc="Inward head switch to Point piece", gaze_target="Point"),
            "Tail": Flyer3DState(15, -45, 0, 45, head_turn_deg=45, gaze_target="OC")
        },
        state_close={
            "Point": Flyer3DState(-35, 35, 0, 405, head_turn_deg=0),
            "OC": Flyer3DState(-15, 0, 0, 405, head_turn_deg=0),
            "IC": Flyer3DState(15, 0, 0, 585, head_turn_deg=0),
            "Tail": Flyer3DState(35, -35, 0, 585, head_turn_deg=0)
        }
    )

    # BLOCK 6: STARDIAN - STARDIAN
    pool["6"] = FormationDefinition(
        code="6", name="Stardian - Stardian", is_block=True, points=2,
        initial_name="Stardian", second_name="Stardian",
        supports_vertical=True,
        subgroup_split="2-Way / 2-Way",
        inter_degrees="180° rotation",
        primary_key_slot="Inside Center",
        key_trigger="Stardian build -> Key -> 180° inter -> Close Stardian",
        head_switch_summary="Wings head switch across center; Centers keep focus on inter picture.",
        coach_tips=["Vertical technique has front piece pop slightly over rear piece."],
        pitfalls_and_busts=["Under-rotating the 180°; failing to achieve clear separation."],
        state_initial={
            "Point": Flyer3DState(-40, 30, 0, 30, head_turn_deg=0),
            "OC": Flyer3DState(-10, 15, 0, 30, head_turn_deg=0),
            "IC": Flyer3DState(10, -15, 0, 210, head_turn_deg=0),
            "Tail": Flyer3DState(40, -30, 0, 210, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-15, 45, 0, 120, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Checking rear piece heading", gaze_target="Tail"),
            "OC": Flyer3DState(-30, 5, 0, 120, head_turn_deg=-20, gaze_target="IC"),
            "IC": Flyer3DState(30, -5, 0, 300, head_turn_deg=20, head_switch_active=True, head_switch_desc="Checking front piece heading", gaze_target="OC"),
            "Tail": Flyer3DState(15, -45, 0, 300, head_turn_deg=30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(10, 35, 0, 210, head_turn_deg=0),
            "OC": Flyer3DState(40, 20, 0, 210, head_turn_deg=0),
            "IC": Flyer3DState(-40, -20, 0, 30, head_turn_deg=0),
            "Tail": Flyer3DState(-10, -35, 0, 30, head_turn_deg=0)
        }
    )

    # BLOCK 7: SIDEBUDDIES - SIDEBUDDIES
    pool["7"] = FormationDefinition(
        code="7", name="Sidebuddies - Sidebuddies", is_block=True, points=2,
        initial_name="Sidebuddies", second_name="Sidebuddies",
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="360° Opposed Spins",
        primary_key_slot="Inside Center",
        key_trigger="Sidebuddies built -> Key -> 360° spins -> Rebuild Sidebuddies",
        head_switch_summary="At 180°, centers head switch across center to calibrate stop timing.",
        coach_tips=["Pieces must turn on their own geometric centerpoints without drifting laterally."],
        pitfalls_and_busts=["Pieces expanding outward, requiring a long closing reach."],
        state_initial={
            "Point": Flyer3DState(-25, 40, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(-25, 0, 0, 0, head_turn_deg=0),
            "IC": Flyer3DState(25, 0, 0, 180, head_turn_deg=0),
            "Tail": Flyer3DState(25, -40, 0, 180, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-35, 15, 0, 180, head_turn_deg=45, head_switch_active=True, head_switch_desc="Cross-checking IC piece", gaze_target="IC"),
            "OC": Flyer3DState(-15, 25, 0, 180, head_turn_deg=30, gaze_target="Tail"),
            "IC": Flyer3DState(15, -25, 0, 360, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Cross-checking OC piece", gaze_target="OC"),
            "Tail": Flyer3DState(35, -15, 0, 360, head_turn_deg=-45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(-25, 40, 0, 360, head_turn_deg=0),
            "OC": Flyer3DState(-25, 0, 0, 360, head_turn_deg=0),
            "IC": Flyer3DState(25, 0, 0, 540, head_turn_deg=0),
            "Tail": Flyer3DState(25, -40, 0, 540, head_turn_deg=0)
        }
    )

    # BLOCK 8: CANADIAN TEE - CANADIAN TEE
    pool["8"] = FormationDefinition(
        code="8", name="Canadian Tee - Canadian Tee", is_block=True, points=2,
        initial_name="Canadian Tee", second_name="Canadian Tee",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Front piece translates over rear piece",
        primary_key_slot="Inside Center",
        key_trigger="Canadian Tee build -> Key -> Front piece slides over rear -> Rebuild",
        head_switch_summary="Point and OC look down as they cross over; IC and Tail look up through burble.",
        coach_tips=["Monopod-like intermediate picture must be achieved cleanly."],
        pitfalls_and_busts=["Front piece dropping onto rear piece (burble collision)."],
        state_initial={
            "Point": Flyer3DState(-30, 45, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-10, 15, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(10, -15, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(30, -45, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(5, 20, 10, 45, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Looking down over rear piece", gaze_target="IC"),
            "OC": Flyer3DState(-15, -10, 10, 45, head_turn_deg=-30, gaze_target="Tail"),
            "IC": Flyer3DState(15, 10, -10, 225, head_turn_deg=30, head_switch_active=True, head_switch_desc="Looking up through clean air", gaze_target="Point"),
            "Tail": Flyer3DState(-5, -20, -10, 225, head_turn_deg=45, gaze_target="OC")
        },
        state_close={
            "Point": Flyer3DState(30, -45, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(10, -15, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(-10, 15, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(-30, 45, 0, 225, head_turn_deg=0)
        }
    )

    # BLOCK 9: CAT + ACCORDION - CAT + ACCORDION
    pool["9"] = FormationDefinition(
        code="9", name="Cat + Accordion - Cat + Accordion", is_block=True, points=2,
        initial_name="Cat + Accordion", second_name="Cat + Accordion",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Subgroups swap positions across center",
        primary_key_slot="Inside Center",
        key_trigger="Cat + Accordion built -> Key -> Subgroups swap -> Rebuild",
        head_switch_summary="Tail head switches to watch cat connection swap.",
        coach_tips=["Subgroups must maintain internal cohesion while swapping positions."],
        pitfalls_and_busts=["Pieces crossing too close and colliding."],
        state_initial={
            "Point": Flyer3DState(-35, 30, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(-10, 30, 0, 0, head_turn_deg=0),
            "IC": Flyer3DState(10, -30, 0, 180, head_turn_deg=0),
            "Tail": Flyer3DState(35, -30, 0, 180, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(10, 40, 0, 45, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Tracking swap with Tail piece", gaze_target="Tail"),
            "OC": Flyer3DState(35, 10, 0, 45, head_turn_deg=-20, gaze_target="IC"),
            "IC": Flyer3DState(-35, -10, 0, 225, head_turn_deg=20, head_switch_active=True, head_switch_desc="Tracking swap with OC piece", gaze_target="OC"),
            "Tail": Flyer3DState(-10, -40, 0, 225, head_turn_deg=30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(35, -30, 0, 180, head_turn_deg=0),
            "OC": Flyer3DState(10, -30, 0, 180, head_turn_deg=0),
            "IC": Flyer3DState(-10, 30, 0, 0, head_turn_deg=0),
            "Tail": Flyer3DState(-35, 30, 0, 0, head_turn_deg=0)
        }
    )

    # BLOCK 10: DIAMOND - BUNYIP
    pool["10"] = FormationDefinition(
        code="10", name="Diamond - Bunyip", is_block=True, points=2,
        initial_name="Diamond", second_name="Bunyip",
        subgroup_split="Pieces break; rotate into Bunyip",
        inter_degrees="180° / 360°",
        primary_key_slot="Inside Center",
        key_trigger="Diamond built -> Key -> Break and rotate -> Close Bunyip",
        head_switch_summary="Wings head switch inward as centers drive the Bunyip shape.",
        coach_tips=["Diamond must break cleanly; all 4 flyers maintain planar trim."],
        pitfalls_and_busts=["Premature Bunyip grip before complete Diamond separation."],
        state_initial={
            "Point": Flyer3DState(0, 50, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(-35, 0, 0, 90, head_turn_deg=0),
            "IC": Flyer3DState(35, 0, 0, 270, head_turn_deg=0),
            "Tail": Flyer3DState(0, -50, 0, 180, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-20, 30, 0, 90, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Tracking OC into Bunyip", gaze_target="OC"),
            "OC": Flyer3DState(-15, -20, 0, 180, head_turn_deg=30, gaze_target="Tail"),
            "IC": Flyer3DState(15, 20, 0, 0, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Tracking Point into Bunyip", gaze_target="Point"),
            "Tail": Flyer3DState(20, -30, 0, 270, head_turn_deg=45, gaze_target="IC")
        },
        state_close={
            "Point": Flyer3DState(-25, 20, 0, 180, head_turn_deg=0),
            "OC": Flyer3DState(-25, -20, 0, 180, head_turn_deg=0),
            "IC": Flyer3DState(25, 20, 0, 0, head_turn_deg=0),
            "Tail": Flyer3DState(25, -20, 0, 0, head_turn_deg=0)
        }
    )

    # BLOCK 11: PHOTON - PHOTON
    pool["11"] = FormationDefinition(
        code="11", name="Photon - Photon", is_block=True, points=2,
        initial_name="Photon", second_name="Photon",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="180° / 360° Vertical Crossover",
        primary_key_slot="Inside Center",
        key_trigger="Photon built -> Key -> Vertical crossover -> Rebuild Photon",
        head_switch_summary="Tail goes under Point and anchors in '2-way star'; IC waits for star target, head switches down.",
        coach_tips=[
            "Tail goes under Point and anchors in the '2-way star' with Point.",
            "IC waits for the '2-way star' target and performs the same task.",
            "Point focuses on IC's gripping hand to close as fast as possible."
        ],
        pitfalls_and_busts=["Tail floating into Point's burble; Point snatching grip before IC is set."],
        state_initial={
            "Point": Flyer3DState(-30, 40, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-10, 15, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(10, -15, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(30, -40, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(0, 30, 12, 180, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Over piece: tracking Tail's star anchor", gaze_target="Tail"),
            "OC": Flyer3DState(-25, 10, 12, 180, head_turn_deg=-20, gaze_target="IC"),
            "IC": Flyer3DState(25, -10, -12, 0, head_turn_deg=20, head_switch_active=True, head_switch_desc="Under piece: tracking Point's gripping hand", gaze_target="Point"),
            "Tail": Flyer3DState(0, -30, -12, 0, head_turn_deg=30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(30, -40, 0, 225, head_turn_deg=0),
            "OC": Flyer3DState(10, -15, 0, 225, head_turn_deg=0),
            "IC": Flyer3DState(-10, 15, 0, 45, head_turn_deg=0),
            "Tail": Flyer3DState(-30, 40, 0, 45, head_turn_deg=0)
        }
    )

    # BLOCK 12: BUNDY - BUNDY
    pool["12"] = FormationDefinition(
        code="12", name="Bundy - Bundy", is_block=True, points=2,
        initial_name="Bundy", second_name="Bundy",
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Front Piece 540° / Rear Piece 360°",
        primary_key_slot="Inside Center",
        key_trigger="Bundy built in line -> IC keys -> Front piece turns 540°, Rear piece turns 360° -> Rebuild perpendicular Bundy",
        head_switch_summary="Centers cross-reference across center during simultaneous 540°/360° turns.",
        coach_tips=[
            "Front piece (Point + OC) executes explosive 540° carve maintaining tight piece axis.",
            "Rear piece (IC + Tail) executes compact 360° spin in place.",
            "Both pieces must match fall rate and close on the perpendicular axis."
        ],
        pitfalls_and_busts=[
            "Front piece blowing out wide during 540° rotation.",
            "Rear piece over-rotating past 360°."
        ],
        state_initial={
            "OC": Flyer3DState(0, 42, 0, 0, head_turn_deg=0),
            "Point": Flyer3DState(0, 15, 0, 0, head_turn_deg=0),
            "IC": Flyer3DState(0, -12, 0, 0, head_turn_deg=0),
            "Tail": Flyer3DState(0, -38, 0, 0, head_turn_deg=0)
        },
        state_inter={
            "OC": Flyer3DState(-18, 25, 0, 180, head_turn_deg=0),
            "Point": Flyer3DState(16, 20, 0, 180, head_turn_deg=0),
            "IC": Flyer3DState(16, -20, 0, 180, head_turn_deg=0),
            "Tail": Flyer3DState(-18, -25, 0, 180, head_turn_deg=0)
        },
        state_close={
            "OC": Flyer3DState(-40, 0, 0, 270, head_turn_deg=0),
            "Point": Flyer3DState(-15, 0, 0, 270, head_turn_deg=0),
            "IC": Flyer3DState(12, 0, 0, 270, head_turn_deg=0),
            "Tail": Flyer3DState(38, 0, 0, 270, head_turn_deg=0)
        }
    )

    # BLOCK 13: MIXED ACCORDION - MIXED ACCORDION
    pool["13"] = FormationDefinition(
        code="13", name="Mixed Accordion - Mixed Accordion", is_block=True, points=2,
        initial_name="Mixed Accordion", second_name="Mixed Accordion",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Reverse direction & rebuild",
        primary_key_slot="Inside Center",
        key_trigger="Mixed Accordion built -> Key -> Break, reverse, rebuild",
        head_switch_summary="Centers hold head switch to guarantee clean inter picture.",
        coach_tips=["Hold the head switch in the inter picture before closing."],
        pitfalls_and_busts=["Rushing the close before completing the reverse move."],
        state_initial={
            "Point": Flyer3DState(-35, 30, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(-15, 0, 0, 180, head_turn_deg=0),
            "IC": Flyer3DState(15, 0, 0, 0, head_turn_deg=0),
            "Tail": Flyer3DState(35, -30, 0, 180, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-25, 45, 0, 90, head_turn_deg=45, head_switch_active=True, head_switch_desc="Holding head switch to track IC", gaze_target="IC"),
            "OC": Flyer3DState(-35, -15, 0, 270, head_turn_deg=30, gaze_target="Tail"),
            "IC": Flyer3DState(35, 15, 0, 90, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Holding head switch to track OC", gaze_target="OC"),
            "Tail": Flyer3DState(25, -45, 0, 270, head_turn_deg=-45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(35, -30, 0, 180, head_turn_deg=0),
            "OC": Flyer3DState(15, 0, 0, 0, head_turn_deg=0),
            "IC": Flyer3DState(-15, 0, 0, 180, head_turn_deg=0),
            "Tail": Flyer3DState(-35, 30, 0, 0, head_turn_deg=0)
        }
    )

    # BLOCK 14: BIPOLE - BIPOLE
    pool["14"] = FormationDefinition(
        code="14", name="Bipole - Bipole", is_block=True, points=2,
        initial_name="Bipole", second_name="Bipole",
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="360° opposing spins",
        primary_key_slot="Inside Center",
        key_trigger="Bipole built -> Key -> 360° piece spins -> Rebuild Bipole",
        head_switch_summary="At 180°, both pieces head switch inward to set closing line.",
        coach_tips=["Piece partners must maintain identical fall rate during high-speed spin."],
        pitfalls_and_busts=["Pieces expanding outward; asymmetric piece spin speed."],
        state_initial={
            "Point": Flyer3DState(-20, 35, 0, 90, head_turn_deg=0),
            "OC": Flyer3DState(-20, -10, 0, 270, head_turn_deg=0),
            "IC": Flyer3DState(20, 10, 0, 90, head_turn_deg=0),
            "Tail": Flyer3DState(20, -35, 0, 270, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-35, 10, 0, 270, head_turn_deg=45, head_switch_active=True, head_switch_desc="Checking IC piece at 180°", gaze_target="IC"),
            "OC": Flyer3DState(-10, 15, 0, 90, head_turn_deg=30, gaze_target="Tail"),
            "IC": Flyer3DState(10, -15, 0, 270, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Checking OC piece at 180°", gaze_target="OC"),
            "Tail": Flyer3DState(35, -10, 0, 90, head_turn_deg=-45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(-20, 35, 0, 450, head_turn_deg=0),
            "OC": Flyer3DState(-20, -10, 0, 630, head_turn_deg=0),
            "IC": Flyer3DState(20, 10, 0, 450, head_turn_deg=0),
            "Tail": Flyer3DState(20, -35, 0, 630, head_turn_deg=0)
        }
    )

    # BLOCK 15: CATERPILLAR - CATERPILLAR
    pool["15"] = FormationDefinition(
        code="15", name="Caterpillar - Caterpillar", is_block=True, points=2,
        initial_name="Caterpillar", second_name="Caterpillar",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Translation into linear caterpillar",
        primary_key_slot="Inside Center",
        key_trigger="Caterpillar built -> Key -> Translate -> Rebuild Caterpillar",
        head_switch_summary="Tail looks along the line of flight to guide rear docking.",
        coach_tips=["Maintain linear alignment; do not allow the caterpillar to buckle."],
        pitfalls_and_busts=["Buckling in the middle; hard docking."],
        state_initial={
            "Point": Flyer3DState(0, 60, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(0, 20, 0, 0, head_turn_deg=0),
            "IC": Flyer3DState(0, -20, 0, 0, head_turn_deg=0),
            "Tail": Flyer3DState(0, -60, 0, 0, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-25, 30, 0, 45, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Tracking OC translation", gaze_target="OC"),
            "OC": Flyer3DState(-10, -10, 0, 45, head_turn_deg=-20, gaze_target="IC"),
            "IC": Flyer3DState(10, 10, 0, 225, head_turn_deg=20, head_switch_active=True, head_switch_desc="Tracking Tail translation", gaze_target="Tail"),
            "Tail": Flyer3DState(25, -30, 0, 225, head_turn_deg=30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(0, -60, 0, 180, head_turn_deg=0),
            "OC": Flyer3DState(0, -20, 0, 180, head_turn_deg=0),
            "IC": Flyer3DState(0, 20, 0, 180, head_turn_deg=0),
            "Tail": Flyer3DState(0, 60, 0, 180, head_turn_deg=0)
        }
    )

    # BLOCK 16: COMPRESSED ACCORDION - BOX
    pool["16"] = FormationDefinition(
        code="16", name="Compressed Accordion - Box", is_block=True, points=2,
        initial_name="Compressed Accordion", second_name="Box",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="180° rotation into open Box",
        primary_key_slot="Inside Center",
        key_trigger="Compressed built -> Key -> 180° rotation -> Close Box",
        head_switch_summary="Centers head switch across box as pieces open up.",
        coach_tips=["Centers must control width so the Box does not open too wide."],
        pitfalls_and_busts=["Over-opening the Box; missing wrist grips."],
        state_initial={
            "Point": Flyer3DState(-25, 25, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-15, -15, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(15, 15, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(25, -25, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-35, 10, 0, 135, head_turn_deg=30, head_switch_active=True, head_switch_desc="Checking Box opening width", gaze_target="IC"),
            "OC": Flyer3DState(-10, 35, 0, 135, head_turn_deg=20, gaze_target="Tail"),
            "IC": Flyer3DState(10, -35, 0, 315, head_turn_deg=-20, head_switch_active=True, head_switch_desc="Checking Box opening width", gaze_target="OC"),
            "Tail": Flyer3DState(35, -10, 0, 315, head_turn_deg=-30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(-30, 30, 0, 225, head_turn_deg=0),
            "OC": Flyer3DState(30, 30, 0, 225, head_turn_deg=0),
            "IC": Flyer3DState(-30, -30, 0, 45, head_turn_deg=0),
            "Tail": Flyer3DState(30, -30, 0, 45, head_turn_deg=0)
        }
    )

    # BLOCK 17: DANISH TEE - MURPHY
    pool["17"] = FormationDefinition(
        code="17", name="Danish Tee - Murphy", is_block=True, points=2,
        initial_name="Danish Tee", second_name="Murphy",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Translation across center",
        primary_key_slot="Inside Center",
        key_trigger="Danish Tee built -> Key -> Cross center -> Close Murphy",
        head_switch_summary="Both pieces head switch across center to spot Murphy alignment.",
        coach_tips=["Smooth translation into a clean, planar Murphy Flake."],
        pitfalls_and_busts=["Over-sliding past the Murphy line."],
        state_initial={
            "Point": Flyer3DState(-35, 30, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-15, 0, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(15, 0, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(35, -30, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-10, 45, 0, 90, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Tracking Murphy line", gaze_target="Tail"),
            "OC": Flyer3DState(-30, 15, 0, 90, head_turn_deg=-20, gaze_target="IC"),
            "IC": Flyer3DState(30, -15, 0, 270, head_turn_deg=20, head_switch_active=True, head_switch_desc="Tracking Murphy line", gaze_target="OC"),
            "Tail": Flyer3DState(10, -45, 0, 270, head_turn_deg=30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(-45, 20, 0, 60, head_turn_deg=0),
            "OC": Flyer3DState(-15, 10, 0, 30, head_turn_deg=0),
            "IC": Flyer3DState(15, -10, 0, 210, head_turn_deg=0),
            "Tail": Flyer3DState(45, -20, 0, 240, head_turn_deg=0)
        }
    )

    # BLOCK 18: ZIRCON - ZIRCON
    pool["18"] = FormationDefinition(
        code="18", name="Zircon - Zircon", is_block=True, points=2,
        initial_name="Zircon", second_name="Zircon",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="180° crossover",
        primary_key_slot="Inside Center",
        key_trigger="Zircon built -> Key -> 180° crossover -> Rebuild Zircon",
        head_switch_summary="Vertical: Over piece head switches down; Under piece head switches up.",
        coach_tips=["Vertical crossover allows pieces to cross paths without blowing out."],
        pitfalls_and_busts=["Collision during crossover; incorrect angle on close."],
        state_initial={
            "Point": Flyer3DState(-30, 35, 0, 30, head_turn_deg=0),
            "OC": Flyer3DState(-15, 0, 0, 30, head_turn_deg=0),
            "IC": Flyer3DState(15, 0, 0, 210, head_turn_deg=0),
            "Tail": Flyer3DState(30, -35, 0, 210, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(10, 25, 10, 120, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Over piece: tracking under piece", gaze_target="IC"),
            "OC": Flyer3DState(-15, 10, 10, 120, head_turn_deg=-30, gaze_target="Tail"),
            "IC": Flyer3DState(15, -10, -10, 300, head_turn_deg=30, head_switch_active=True, head_switch_desc="Under piece: tracking over piece", gaze_target="OC"),
            "Tail": Flyer3DState(-10, -25, -10, 300, head_turn_deg=45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(30, -35, 0, 210, head_turn_deg=0),
            "OC": Flyer3DState(15, 0, 0, 210, head_turn_deg=0),
            "IC": Flyer3DState(-15, 0, 0, 30, head_turn_deg=0),
            "Tail": Flyer3DState(-30, 35, 0, 30, head_turn_deg=0)
        }
    )

    # BLOCK 19: RITZ - ICE PICK
    pool["19"] = FormationDefinition(
        code="19", name="Ritz - Ice Pick", is_block=True, points=2,
        initial_name="Ritz", second_name="Ice Pick",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="180° spin to Ice Pick",
        primary_key_slot="Inside Center",
        key_trigger="Ritz built -> Key -> 180° rotation -> Close Ice Pick",
        head_switch_summary="Centers head switch across center to verify Ice Pick shape.",
        coach_tips=["Ice Pick requires precise grip presentation from wings."],
        pitfalls_and_busts=["Missing the Ice Pick wrist grips; level mismatch."],
        state_initial={
            "Point": Flyer3DState(-25, 40, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-35, 0, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(35, 0, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(25, -40, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(-10, 45, 0, 135, head_turn_deg=30, head_switch_active=True, head_switch_desc="Tracking Ice Pick build", gaze_target="IC"),
            "OC": Flyer3DState(-30, 15, 0, 135, head_turn_deg=20, gaze_target="Tail"),
            "IC": Flyer3DState(30, -15, 0, 315, head_turn_deg=-20, head_switch_active=True, head_switch_desc="Tracking Ice Pick build", gaze_target="OC"),
            "Tail": Flyer3DState(10, -45, 0, 315, head_turn_deg=-30, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(0, 45, 0, 225, head_turn_deg=0),
            "OC": Flyer3DState(-35, 0, 0, 225, head_turn_deg=0),
            "IC": Flyer3DState(35, 0, 0, 45, head_turn_deg=0),
            "Tail": Flyer3DState(0, -45, 0, 45, head_turn_deg=0)
        }
    )

    # BLOCK 20: PIVER - VIPER
    pool["20"] = FormationDefinition(
        code="20", name="Piver - Viper", is_block=True, points=2,
        initial_name="Piver", second_name="Viper",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Rotate and translate across center",
        primary_key_slot="Inside Center",
        key_trigger="Piver built -> Key -> Cross center -> Close Viper",
        head_switch_summary="Wings head switch across center; Centers keep focus on piece line.",
        coach_tips=["Vertical option allows smooth over/under crossover without wide bows."],
        pitfalls_and_busts=["Overshooting Viper build; failing to stop momentum."],
        state_initial={
            "Point": Flyer3DState(-35, 30, 0, 45, head_turn_deg=0),
            "OC": Flyer3DState(-15, -10, 0, 45, head_turn_deg=0),
            "IC": Flyer3DState(15, 10, 0, 225, head_turn_deg=0),
            "Tail": Flyer3DState(35, -30, 0, 225, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(15, 20, 10, 135, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Over piece: looking down into Viper", gaze_target="IC"),
            "OC": Flyer3DState(-10, 10, 10, 135, head_turn_deg=-30, gaze_target="Tail"),
            "IC": Flyer3DState(10, -10, -10, 315, head_turn_deg=30, head_switch_active=True, head_switch_desc="Under piece: looking up into Viper", gaze_target="OC"),
            "Tail": Flyer3DState(-15, -20, -10, 315, head_turn_deg=45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(35, -30, 0, 225, head_turn_deg=0),
            "OC": Flyer3DState(15, 10, 0, 225, head_turn_deg=0),
            "IC": Flyer3DState(-15, -10, 0, 45, head_turn_deg=0),
            "Tail": Flyer3DState(-35, 30, 0, 45, head_turn_deg=0)
        }
    )

    # BLOCK 21: ZIG ZAG - MARQUIS (THE SIGNATURE 4-WAY BLOCK)
    pool["21"] = FormationDefinition(
        code="21", name="Zig Zag - Marquis", is_block=True, points=2,
        initial_name="Zig Zag", second_name="Marquis",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Centers step out; wings cross over with 180° turns",
        primary_key_slot="Inside Center",
        key_trigger="Zig Zag built solid -> Key -> Step out & crossover -> Close Marquis",
        key_method="Visual nod from Inside Center",
        head_switch_summary="As centers step out, they must stop outward momentum as wings cross. Point and OC look down; IC and Tail look up.",
        coach_tips=[
            "Vertical Technique: Point and OC go OVER. IC and Tail go UNDER.",
            "Centers' first move is to step out at an angle, then STOP momentum outwards.",
            "When outsides cross, they begin stopping as they cross (Start-Coast-Stop).",
            "If centers don't stop outward drift, pieces go too far and block will not close!"
        ],
        pitfalls_and_busts=[
            "Centers continuing to slide outward (blows out the close).",
            "Wings colliding during crossover.",
            "Premature grip taking before complete separation."
        ],
        state_initial={
            "Point": Flyer3DState(-45, 35, 0, 45, head_turn_deg=0, right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-15, 10, 0, 45, head_turn_deg=0, left_grip="IC Left Wrist"),
            "IC": Flyer3DState(15, -10, 0, 225, head_turn_deg=0, right_grip="OC Right Wrist"),
            "Tail": Flyer3DState(45, -35, 0, 225, head_turn_deg=0, left_grip="IC Right Wrist")
        },
        state_inter={
            "Point": Flyer3DState(10, 25, 15, 135, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Over piece crossing: head switch down to IC", gaze_target="IC"),
            "OC": Flyer3DState(-25, 20, 15, 135, head_turn_deg=-30, head_switch_active=True, head_switch_desc="Stepping out & stopping momentum", gaze_target="Tail"),
            "IC": Flyer3DState(25, -20, -15, 315, head_turn_deg=30, head_switch_active=True, head_switch_desc="Stepping out & stopping momentum; looking up", gaze_target="OC"),
            "Tail": Flyer3DState(-10, -25, -15, 315, head_turn_deg=45, head_switch_active=True, head_switch_desc="Under piece crossing: head switch up to Point", gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(35, -25, 0, 225, head_turn_deg=0, right_grip="IC Left Wrist"),
            "OC": Flyer3DState(20, 20, 0, 225, head_turn_deg=0, left_grip="Point Left Wrist"),
            "IC": Flyer3DState(-20, -20, 0, 45, head_turn_deg=0, right_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(-35, 25, 0, 45, head_turn_deg=0, left_grip="OC Right Wrist")
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Over Piece Wing", "Cross over under piece; rotate 180° into Marquis.", "Takes IC wrist on close.", "Head switch down to spot IC during crossover.", "180° Crossover", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Over Piece Center", "Step out at angle; STOP outward momentum as Point crosses.", "Connects with Point.", "Looks down and across at Tail.", "Step out & brake", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Under Piece Center & Keyer", "Key Build 1; step out low; STOP outward drift as Tail crosses.", "Connects with Tail.", "Looks up and across at OC.", "Step out & brake", "PRIMARY KEY Build 1"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Under Piece Wing", "Drive under front piece; rotate 180° into Marquis.", "Takes OC wrist on close.", "Head switch up to spot Point during crossover.", "180° Crossover", "Reacts on close")
        }
    )

    # BLOCK 22: TEE - CHINESE TEE
    pool["22"] = FormationDefinition(
        code="22", name="Tee - Chinese Tee", is_block=True, points=2,
        initial_name="Tee", second_name="Chinese Tee",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="180° crossover",
        primary_key_slot="Inside Center",
        key_trigger="Tee built -> Key -> 180° crossover -> Close Chinese Tee",
        head_switch_summary="Front piece head switches down; rear piece head switches up during 180° rotation.",
        coach_tips=[
            "Evaluate build axis vs previous formation center.",
            "Front piece pops slightly; rear piece stays flat underneath."
        ],
        pitfalls_and_busts=["Front piece hitting rear piece burble; over-rotating."],
        state_initial={
            "Point": Flyer3DState(-30, 40, 0, 0, head_turn_deg=0),
            "OC": Flyer3DState(-10, 10, 0, 90, head_turn_deg=0),
            "IC": Flyer3DState(10, -10, 0, 270, head_turn_deg=0),
            "Tail": Flyer3DState(30, -40, 0, 180, head_turn_deg=0)
        },
        state_inter={
            "Point": Flyer3DState(15, 25, 12, 90, head_turn_deg=-45, head_switch_active=True, head_switch_desc="Over piece: looking down into Chinese Tee", gaze_target="IC"),
            "OC": Flyer3DState(-15, 20, 12, 180, head_turn_deg=-30, gaze_target="Tail"),
            "IC": Flyer3DState(15, -20, -12, 0, head_turn_deg=30, head_switch_active=True, head_switch_desc="Under piece: looking up into Chinese Tee", gaze_target="OC"),
            "Tail": Flyer3DState(-15, -25, -12, 270, head_turn_deg=45, gaze_target="Point")
        },
        state_close={
            "Point": Flyer3DState(30, -40, 0, 180, head_turn_deg=0),
            "OC": Flyer3DState(10, -10, 0, 270, head_turn_deg=0),
            "IC": Flyer3DState(-10, 10, 0, 90, head_turn_deg=0),
            "Tail": Flyer3DState(-30, 40, 0, 0, head_turn_deg=0)
        }
    )

    return pool


# Global database instance
DIVE_POOL: Dict[str, FormationDefinition] = _build_dive_pool()


def get_formation(code: str) -> Optional[FormationDefinition]:
    """Look up a formation definition by code (case-insensitive)."""
    return DIVE_POOL.get(code.strip().upper())


def get_all_formations() -> List[FormationDefinition]:
    """Return all formations sorted by category (Randoms A-Q, then Blocks 1-22)."""
    randoms = [f for f in DIVE_POOL.values() if not f.is_block]
    blocks = [f for f in DIVE_POOL.values() if f.is_block]
    randoms.sort(key=lambda x: x.code)
    blocks.sort(key=lambda x: int(x.code) if x.code.isdigit() else 999)
    return randoms + blocks
