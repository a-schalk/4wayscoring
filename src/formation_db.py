"""
FAI 4-Way Formation Skydiving Dive Pool & Technique Database
Comprehensive database containing all 16 Randoms (A-Q) and 22 Blocks (1-22).
Directly derived from the ground-truth diagrams of the SDC Rhythm XP Continuity Booklet.
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
class PieceKinematics:
    """Kinematic movement definition for a piece during block transition."""
    slots: List[str]                  # e.g. ["Point", "OC"]
    rotation_deg: float = 0.0         # Rotation in degrees (e.g. +360, -360, +540, +180, -90)
    pivot_mode: str = "center"        # "center" (piece midpoint), or slot name e.g. "Point"
    vertical_arch: float = 0.0        # Z arch during inter (e.g. +16.0 for over, -16.0 for under)


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
    
    # Kinematic Piece Definitions
    pieces: List[PieceKinematics] = field(default_factory=list)
    pieces_vertical: List[PieceKinematics] = field(default_factory=list)

    # Slot Details (Point, OC, IC, Tail, Videographer)
    slot_details: Dict[str, SlotDetail] = field(default_factory=dict)


def get_block_piece_kinematics(
    formation: FormationDefinition, use_vertical: bool = False
) -> List[PieceKinematics]:
    """Resolves or dynamically computes exact piece kinematics for a block."""
    if not formation.is_block:
        return []

    if use_vertical and formation.pieces_vertical:
        return formation.pieces_vertical
    if formation.pieces:
        return formation.pieces

    # Dynamic fallback
    return [
        PieceKinematics(slots=["Point", "OC"], rotation_deg=360.0),
        PieceKinematics(slots=["IC", "Tail"], rotation_deg=360.0)
    ]


# Standard SDC Rhythm XP Colors (as shown in Continuity Booklet)
COLOR_POINT = "#EF4444"    # Red (Point)
COLOR_OC = "#10B981"       # Green (Outside Center)
COLOR_IC = "#3B82F6"       # Blue (Inside Center)
COLOR_TAIL = "#EAB308"     # Yellow (Tail)
COLOR_VIDEO = "#A855F7"    # Purple (Videographer)


def _build_dive_pool() -> Dict[str, FormationDefinition]:
    pool: Dict[str, FormationDefinition] = {}

    # =========================================================================
    # 16 RANDOMS (A through Q)
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
            "Point": Flyer3DState(2.0, 56.8, 0.0, 234.5, grippers_presented=['Left Wrist', 'Right Wrist']),
            "OC": Flyer3DState(-21.9, 13.0, 0.0, 345.0, head_turn_deg=-20, gaze_target="Point", right_grip="Point Left Wrist"),
            "IC": Flyer3DState(29.1, -14.3, 0.0, 82.2, head_turn_deg=20, gaze_target="Point", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(-9.2, -55.5, 0.0, 342.6, gaze_target="Point", left_grip="OC Left Ankle", right_grip="IC Right Ankle"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Wing / Outfacing Anchor",
                                "Fly to front apex; present level wrists into clean air; hold heading 0\u00b0.",
                                "Presents Left and Right Wrists. Takes no grips.",
                                "Head held high; look at horizon; do not look down or back at centers.",
                                "0\u00b0 In-Place", "Waits for key; launches into next move instantly"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Center Hub",
                                "Fly to left shoulder of Point; take Point's left wrist; set 45\u00b0 angle.",
                                "Right hand takes Point's Left Wrist. Presents rear ankles/hips to Tail.",
                                "Head turned 20\u00b0 toward Point's wrist and cross-references IC across center.",
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
                                "0\u00b0 Drive forward", "Reacts explosively to IC's key"),
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
            "Point": Flyer3DState(-5.0, 31.5, 0.0, 88.7, head_turn_deg=-20, gaze_target="Tail", left_grip="OC Left Wrist"),
            "OC": Flyer3DState(-52.9, -2.9, 0.0, 96.4, head_turn_deg=20, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(52.6, 2.2, 0.0, 90.5, head_turn_deg=20, gaze_target="OC", left_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(5.2, -30.8, 0.0, 277.9, head_turn_deg=-20, gaze_target="Point", right_grip="Point Left Ankle"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Forward Stagger Apex",
                                "Hold upper left diamond point; maintain 20\u00b0 heading.",
                                "Takes OC wrist; presents ankle.",
                                "References Tail across the diagonal.",
                                "Offset slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Lateral Link",
                                "Bridge Point and IC; lock arm-to-wrist grip.",
                                "Takes IC wrist; presents wrist to Point.",
                                "Looks inward toward IC.",
                                "Lateral trim", "Assists key confirmation"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Lateral Link & Keyer",
                                "Hold center offset; take Tail wrist; scan whole formation.",
                                "Takes Tail wrist; presents wrist to OC.",
                                "Cross-references OC and checks Point.",
                                "Center anchor", "PRIMARY KEY: Keys upon grip lock"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Stagger Apex",
                                "Hold rear right diamond point; balance fall rate.",
                                "Takes Point ankle; presents wrist to IC.",
                                "Locks gaze with Point across center.",
                                "Offset drive", "Explosive release"),
        }
    )

    # RANDOM C: MURPHY FLAKE
    pool["C"] = FormationDefinition(
        code="C", name="Murphy Flake", is_block=False, points=1,
        initial_name="Murphy Flake",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Flake line established with alternating hand-to-wrist connections",
        key_method="Visual nod",
        head_switch_summary="All flyers look across formation. Centers keep shoulders square while checking wings.",
        coach_tips=[
        "Maintain wide planar spacing; avoid accordion folding.",
        "Flyers must fly their own bodies into position before taking grips."
],
        pitfalls_and_busts=[
        "Snatching wrists from too far away, causing the line to curve or potato-chip."
],
        state_initial={
            "Point": Flyer3DState(-4.4, 60.5, 0.0, 155.7, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-23.7, -2.1, 0.0, 234.5, head_turn_deg=-30, gaze_target="Point", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(22.2, -3.7, 0.0, 351.8, head_turn_deg=30, gaze_target="Tail", right_grip="OC Right Wrist"),
            "Tail": Flyer3DState(5.9, -54.7, 0.0, 39.7, gaze_target="IC", left_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Outer Flake Wing",
                                "Fly outer left perimeter; maintain flake heading.",
                                "Takes OC wrist.",
                                "Looks inward at OC.",
                                "Perimeter slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Flake Link",
                                "Connect Point with center; match fall rate.",
                                "Takes IC wrist; presents wrist to Point.",
                                "Checks Point and IC simultaneously.",
                                "Planar trim", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Flake Anchor & Keyer",
                                "Anchor middle flake; verify grips across line.",
                                "Takes OC wrist; presents wrist to Tail.",
                                "Looks across flake to verify both wings.",
                                "Central anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Outer Flake Wing",
                                "Fly outer right perimeter; anchor the rear.",
                                "Takes IC wrist.",
                                "Looks inward at IC.",
                                "Perimeter drive", "Reacts on key"),
        }
    )

    # RANDOM D: YUAN
    pool["D"] = FormationDefinition(
        code="D", name="Yuan", is_block=False, points=1,
        initial_name="Yuan",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Asymmetrical grips locked on ankles and wrists",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Point head switches to present ankle; IC monitors Point's leg grip.",
        coach_tips=[
        "Asymmetric geometry requires IC to hold a rock-steady fall rate while Point presents."
],
        pitfalls_and_busts=[
        "Point swinging legs out of reach; Centers over-reaching."
],
        state_initial={
            "Point": Flyer3DState(-11.1, 32.6, 0.0, 133.0, head_turn_deg=45, gaze_target="OC", grippers_presented=['Left Ankle']),
            "OC": Flyer3DState(-33.8, 8.9, 0.0, 311.7, head_turn_deg=-20, gaze_target="Point", right_grip="Point Left Ankle"),
            "IC": Flyer3DState(39.8, 1.1, 0.0, 155.8, head_turn_deg=30, gaze_target="Tail", left_grip="OC Left Wrist"),
            "Tail": Flyer3DState(5.1, -42.6, 0.0, 272.9, head_turn_deg=-30, gaze_target="IC", right_grip="IC Right Ankle"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Asymmetric Wing",
                                "Turn 90\u00b0; present leg clean into OC space.",
                                "Presents Left Ankle.",
                                "Head switch right to verify OC grip.",
                                "90\u00b0 Turn", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Forward Link",
                                "Catch Point's ankle gently; do not pull.",
                                "Takes Point Ankle; presents wrist.",
                                "Looks down at Point ankle.",
                                "Forward step", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Pivot & Keyer",
                                "Hold center base; connect OC and Tail.",
                                "Takes OC wrist; presents ankle.",
                                "Scans Point and Tail.",
                                "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Wing",
                                "Take IC ankle; stabilize rear quadrant.",
                                "Takes IC Ankle.",
                                "Looks inward at IC.",
                                "Rear drive", "Reacts on key"),
        }
    )

    # RANDOM E: MEEKER
    pool["E"] = FormationDefinition(
        code="E", name="Meeker", is_block=False, points=1,
        initial_name="Meeker",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Compact compressed center built with wings in position",
        key_method="Visual nod",
        head_switch_summary="Centers lock eyes in tight compression. Wings cross-reference across center.",
        coach_tips=[
        "Centers must compress tight; wings stay wide enough not to funnel the center."
],
        pitfalls_and_busts=[
        "Centers pushing away from each other; wings lagging behind."
],
        state_initial={
            "Point": Flyer3DState(0.1, 43.0, 0.0, 89.1, gaze_target="Tail", left_grip="OC Right Wrist"),
            "OC": Flyer3DState(-30.2, 3.5, 0.0, 136.5, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(28.7, -4.6, 0.0, 129.1, gaze_target="OC", left_grip="OC Right Wrist"),
            "Tail": Flyer3DState(1.3, -41.8, 0.0, 271.7, gaze_target="Point", right_grip="IC Left Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Apex",
                                "Fly to front apex; take OC wrist.",
                                "Takes OC wrist.",
                                "Looks down through center at Tail.",
                                "Forward slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Center Compression",
                                "Face IC directly; lock tight center.",
                                "Takes IC wrist; presents to Point.",
                                "Direct eye contact with IC.",
                                "Center compression", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Center Compression & Keyer",
                                "Face OC directly; verify both wing grips.",
                                "Takes OC wrist; presents to Tail.",
                                "Direct eye contact with OC; peripheral on wings.",
                                "Center compression", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Apex",
                                "Fly to rear apex; take IC wrist.",
                                "Takes IC wrist.",
                                "Looks up through center at Point.",
                                "Rear drive", "Reacts on key"),
        }
    )

    # RANDOM F: OPEN ACCORDION
    pool["F"] = FormationDefinition(
        code="F", name="Open Accordion", is_block=False, points=1,
        initial_name="Open Accordion",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Zig-zag line complete with equal spacing across all 4 flyers",
        key_method="Visual nod",
        head_switch_summary="Strict clone cross-referencing: Point references Tail; OC references IC.",
        coach_tips=[
        "Do not let the accordion compress into a straight line.",
        "Cross-reference your clone to match angles and levels exactly."
],
        pitfalls_and_busts=[
        "Folding into a ball; level discrepancy between outer flyers."
],
        state_initial={
            "Point": Flyer3DState(-0.4, 53.0, 0.0, 62.0, head_turn_deg=10, gaze_target="Tail", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-35.7, -2.0, 0.0, 245.0, head_turn_deg=-10, gaze_target="IC", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(32.8, 4.0, 0.0, 57.5, head_turn_deg=10, gaze_target="OC", right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(3.3, -55.0, 0.0, 236.4, head_turn_deg=-10, gaze_target="Point", left_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Outer Accordion Wing",
                                "Hold 45\u00b0 heading; grip OC wrist.",
                                "Takes OC wrist.",
                                "Cross-references Tail on opposite end.",
                                "Radial slide", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Accordion Link",
                                "Hold 225\u00b0 heading; connect Point and IC.",
                                "Takes IC wrist; presents to Point.",
                                "Looks at IC.",
                                "Angle maintenance", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Accordion Link & Keyer",
                                "Hold 45\u00b0 heading; connect OC and Tail.",
                                "Takes Tail wrist; presents to OC.",
                                "Looks across at OC; verifies wings.",
                                "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Outer Accordion Wing",
                                "Hold 225\u00b0 heading; grip IC wrist.",
                                "Takes IC wrist.",
                                "Cross-references Point across line.",
                                "Radial drive", "Reacts on key"),
        }
    )

    # RANDOM G: CATACCORD
    pool["G"] = FormationDefinition(
        code="G", name="Cataccord", is_block=False, points=1,
        initial_name="Cataccord",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Tail secures double leg grips on IC and OC while Point closes accordion",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Tail looks down at legs to ensure clean cat grips; Point references centers.",
        coach_tips=[
        "Tail must not pull backward on centers' legs; fly your chest forward into the cat."
],
        pitfalls_and_busts=[
        "Tail pulling centers apart; Point over-sliding."
],
        state_initial={
            "Point": Flyer3DState(-13.0, 57.0, 0.0, 66.5, gaze_target="IC", left_grip="OC Right Wrist"),
            "OC": Flyer3DState(-8.1, 26.9, 0.0, 67.0, head_turn_deg=-30, gaze_target="Point", right_grip="Point Left Wrist"),
            "IC": Flyer3DState(15.4, -11.5, 0.0, 156.2, head_turn_deg=30, gaze_target="Point", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(5.7, -72.5, 0.0, 34.8, gaze_target="IC", left_grip="OC Left Ankle", right_grip="IC Right Ankle"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Accordion Apex",
                                "Present/take with centers in accordion.",
                                "Takes OC wrist.",
                                "Looks at centers.",
                                "Front setup", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Left Cat Front",
                                "Hold steady leg presentation for Tail.",
                                "Presents ankle to Tail.",
                                "Looks at Point.",
                                "Leg presentation", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Right Cat Front & Keyer",
                                "Hold steady leg presentation; verify Tail grips.",
                                "Presents ankle to Tail.",
                                "Peripheral check on Tail.",
                                "Center keyer", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Cat Flyer (Double Leg Grips)",
                                "Drive in infacing; take both centers' ankles.",
                                "Takes OC & IC ankles.",
                                "Looks at centers' hips.",
                                "Cat drive", "Reacts on key"),
        }
    )

    # RANDOM H: BOW
    pool["H"] = FormationDefinition(
        code="H", name="Bow", is_block=False, points=1,
        initial_name="Bow",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Classic bow configuration built with interlocking center grips",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Centers face diagonally; wings look inward at center intersection.",
        coach_tips=[
        "Standard exit formation. Keep it compact; wings must stay close to centers."
],
        pitfalls_and_busts=[
        "Centers blowing apart on exit; wings funneling the center."
],
        state_initial={
            "Point": Flyer3DState(3.1, 53.5, 0.0, 93.6, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-22.9, 1.7, 0.0, 9.9, head_turn_deg=45, gaze_target="IC", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(19.1, 2.4, 0.0, 171.4, head_turn_deg=-45, gaze_target="OC", right_grip="OC Right Wrist"),
            "Tail": Flyer3DState(0.7, -57.6, 0.0, 179.9, gaze_target="IC", left_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Bow Wing",
                                "Launch exit; grip OC wrist.",
                                "Takes OC wrist.",
                                "Looks inward at OC.",
                                "Bow wing", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Outside Bow Center",
                                "Float exit; lock center bow with IC.",
                                "Takes IC wrist.",
                                "Looks at IC.",
                                "Center exit", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Inside Bow Center & Keyer",
                                "Sneak low on exit; lock bow with OC.",
                                "Takes OC wrist.",
                                "Looks at OC.",
                                "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Bow Wing",
                                "Drop exit; grip IC wrist.",
                                "Takes IC wrist.",
                                "Looks inward at IC.",
                                "Bow tail", "Reacts on key"),
        }
    )

    # RANDOM J: DONUT
    pool["J"] = FormationDefinition(
        code="J", name="Donut", is_block=False, points=1,
        initial_name="Donut",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Closed donut ring with alternating wrist/arm grips",
        key_method="Visual nod from Inside Center",
        head_switch_summary="All flyers look across center of circle at diagonal clone.",
        coach_tips=[
        "Maintain circular quadrant symmetry. Do not allow donut to flatten."
],
        pitfalls_and_busts=[
        "Unequal circle diameter; one side collapsing inward."
],
        state_initial={
            "Point": Flyer3DState(0.5, 43.5, 0.0, 86.7, head_turn_deg=-15, gaze_target="Tail", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-42.9, -1.1, 0.0, 1.6, head_turn_deg=-15, gaze_target="IC", right_grip="Tail Left Wrist"),
            "IC": Flyer3DState(41.8, 1.0, 0.0, 176.7, head_turn_deg=15, gaze_target="OC", left_grip="Point Right Wrist"),
            "Tail": Flyer3DState(0.5, -43.4, 0.0, 268.6, head_turn_deg=-15, gaze_target="Point", right_grip="IC Left Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Donut Quadrant 1",
                                "Hold circle arc; take OC wrist.",
                                "Takes OC wrist.",
                                "Looks across at Tail.",
                                "Circular arc", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Donut Quadrant 2",
                                "Hold circle arc; take Tail wrist.",
                                "Takes Tail wrist.",
                                "Looks across at IC.",
                                "Circular arc", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Donut Quadrant 3 & Keyer",
                                "Hold circle arc; take Point wrist.",
                                "Takes Point wrist.",
                                "Looks across at OC.",
                                "Circular arc", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Donut Quadrant 4",
                                "Hold circle arc; take IC wrist.",
                                "Takes IC wrist.",
                                "Looks across at Point.",
                                "Circular arc", "Reacts on key"),
        }
    )

    # RANDOM K: HOOK
    pool["K"] = FormationDefinition(
        code="K", name="Hook", is_block=False, points=1,
        initial_name="Hook",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Offset hook shape with hand-to-leg grips locked",
        key_method="Visual nod",
        head_switch_summary="Flyers taking leg grips head switch down/back to confirm leg position.",
        coach_tips=[
        "Leg grippers must be presented firmly; takers fly to the leg rather than pulling."
],
        pitfalls_and_busts=[
        "Kicking legs away; pulling taker off heading."
],
        state_initial={
            "Point": Flyer3DState(-0.5, 54.5, 0.0, 115.7, head_turn_deg=30, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-19.6, 8.9, 0.0, 199.5, head_turn_deg=-20, gaze_target="Point", left_grip="IC Right Ankle"),
            "IC": Flyer3DState(24.9, -14.4, 0.0, 41.5, head_turn_deg=-30, gaze_target="Tail", left_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(-4.8, -49.0, 0.0, 316.3, head_turn_deg=20, gaze_target="IC", right_grip="Point Left Ankle"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Hook Front",
                                "Hold 0\u00b0 heading; take OC wrist.",
                                "Takes OC wrist.",
                                "Looks at OC.",
                                "Front hook", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Hook Center",
                                "Take IC ankle with left hand.",
                                "Takes IC ankle.",
                                "Looks down at IC ankle.",
                                "Center hook", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Hook Center & Keyer",
                                "Present ankle to OC; take Tail wrist.",
                                "Takes Tail wrist.",
                                "Looks at Tail.",
                                "Center anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Hook Rear",
                                "Take Point ankle; hold 180\u00b0.",
                                "Takes Point ankle.",
                                "Looks up at Point ankle.",
                                "Rear hook", "Reacts on key"),
        }
    )

    # RANDOM L: ADDER
    pool["L"] = FormationDefinition(
        code="L", name="Adder", is_block=False, points=1,
        initial_name="Adder",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Stepped zig-zag complete along the Point-Tail axis",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Point and Tail lock on central line; Centers reference each other.",
        coach_tips=[
        "Strict adherence to the Magic Point-Tail line; keep centers compact."
],
        pitfalls_and_busts=[
        "Centers sliding wide, stretching wings into reaching."
],
        state_initial={
            "Point": Flyer3DState(4.2, 45.1, 0.0, 250.7, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-34.5, 2.4, 0.0, 16.5, head_turn_deg=30, gaze_target="IC", left_grip="IC Left Wrist"),
            "IC": Flyer3DState(24.4, 1.7, 0.0, 159.0, head_turn_deg=-30, gaze_target="OC", right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(5.9, -49.1, 0.0, 43.4, gaze_target="IC", left_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Adder Front",
                                "Stay on Point-Tail axis; take OC wrist.",
                                "Takes OC wrist.",
                                "Looks at OC.",
                                "Axis anchor", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Adder Left Center",
                                "Inface rearward; connect Point and IC.",
                                "Takes IC wrist.",
                                "Looks across at IC.",
                                "Center link", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Adder Right Center & Keyer",
                                "Inface forward; connect OC and Tail.",
                                "Takes Tail wrist.",
                                "Looks across at OC.",
                                "Center link", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Adder Rear",
                                "Stay on Point-Tail axis; take IC wrist.",
                                "Takes IC wrist.",
                                "Looks at IC.",
                                "Axis anchor", "Reacts on key"),
        }
    )

    # RANDOM M: STAR
    pool["M"] = FormationDefinition(
        code="M", name="Star", is_block=False, points=1,
        initial_name="Star",
        subgroup_split="",
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
            "Point": Flyer3DState(-0.7, 48.7, 0.0, 358.7, gaze_target="Tail", left_grip="OC Right Wrist", right_grip="IC Left Wrist"),
            "OC": Flyer3DState(-48.0, -0.2, 0.0, 270.8, gaze_target="IC", left_grip="Tail Right Wrist", right_grip="Point Left Wrist"),
            "IC": Flyer3DState(48.6, 0.4, 0.0, 90.5, gaze_target="OC", left_grip="Point Right Wrist", right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(0.0, -48.9, 0.0, 182.4, gaze_target="Point", left_grip="IC Right Wrist", right_grip="OC Left Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "North Star Arm",
                                "Fly directly South to (0, 42); take OC and IC wrists.",
                                "Takes OC & IC wrists.",
                                "Locks eyes with Tail across center.",
                                "Radial in-place", "Simultaneous flash release"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "West Star Arm",
                                "Fly directly East to (-42, 0); take Point and Tail wrists.",
                                "Takes Point & Tail wrists.",
                                "Locks eyes with IC across center.",
                                "Radial in-place", "Simultaneous flash release"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "East Star Arm & Keyer",
                                "Fly directly West to (42, 0); take Point and Tail wrists.",
                                "Takes Point & Tail wrists.",
                                "Locks eyes with OC across center.",
                                "Radial in-place", "PRIMARY KEY: Keys on 4th grip touch"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "South Star Arm",
                                "Fly directly North to (0, -42); take OC and IC wrists.",
                                "Takes OC & IC wrists.",
                                "Locks eyes with Point across center.",
                                "Radial in-place", "Simultaneous flash release"),
        }
    )

    # RANDOM N: CRANK
    pool["N"] = FormationDefinition(
        code="N", name="Crank", is_block=False, points=1,
        initial_name="Crank",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Offset rectangular box grips established without torquing",
        key_method="Visual nod",
        head_switch_summary="Centers reference each other; wings look along grip line.",
        coach_tips=[
        "High rotational torque potential. Maintain quiet air; do not twist grips."
],
        pitfalls_and_busts=[
        "Torquing the box into a spin; level discrepancies."
],
        state_initial={
            "Point": Flyer3DState(-15.7, 53.2, 0.0, 16.2, head_turn_deg=30, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-31.3, 7.9, 0.0, 105.0, head_turn_deg=-30, gaze_target="Tail", left_grip="Tail Left Wrist"),
            "IC": Flyer3DState(27.0, -7.6, 0.0, 102.3, head_turn_deg=-30, gaze_target="Point", left_grip="Point Left Wrist"),
            "Tail": Flyer3DState(20.1, -53.5, 0.0, 198.4, head_turn_deg=30, gaze_target="IC", right_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Crank Wing",
                                "Hold 90\u00b0 heading; take OC wrist.",
                                "Takes OC wrist.",
                                "Looks at OC.",
                                "Offset box", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Crank Center",
                                "Hold 0\u00b0 heading; take Tail wrist.",
                                "Takes Tail wrist.",
                                "Looks at Tail.",
                                "Offset box", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Crank Center & Keyer",
                                "Hold 180\u00b0 heading; take Point wrist.",
                                "Takes Point wrist.",
                                "Looks at Point.",
                                "Offset box", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Crank Wing",
                                "Hold 270\u00b0 heading; take IC wrist.",
                                "Takes IC wrist.",
                                "Looks at IC.",
                                "Offset box", "Reacts on key"),
        }
    )

    # RANDOM O: SATELLITE
    pool["O"] = FormationDefinition(
        code="O", name="Satellite", is_block=False, points=1,
        initial_name="Satellite",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="Opposed satellite ring complete; level across all flyers",
        key_method="Visual nod",
        head_switch_summary="All flyers check diagonal clone for level matching.",
        coach_tips=[
        "Clone cross-referencing is critical for stability."
],
        pitfalls_and_busts=[
        "Over-rotation; dropping outside elbows."
],
        state_initial={
            "Point": Flyer3DState(-0.5, 39.3, 0.0, 37.9, head_turn_deg=20, gaze_target="Tail", right_grip="IC Left Wrist"),
            "OC": Flyer3DState(-36.2, -9.7, 0.0, 218.3, head_turn_deg=20, gaze_target="IC", left_grip="Point Left Wrist"),
            "IC": Flyer3DState(37.4, 11.0, 0.0, 122.9, head_turn_deg=-20, gaze_target="OC", left_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(-0.7, -40.6, 0.0, 128.2, head_turn_deg=20, gaze_target="Point", right_grip="OC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Opposed Satellite Arm",
                                "Hold 315\u00b0; take IC wrist.",
                                "Takes IC wrist.",
                                "Looks at Tail.",
                                "Opposed arc", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Opposed Satellite Arm",
                                "Hold 225\u00b0; take Point wrist.",
                                "Takes Point wrist.",
                                "Looks at IC.",
                                "Opposed arc", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Opposed Satellite Arm & Keyer",
                                "Hold 45\u00b0; take Tail wrist.",
                                "Takes Tail wrist.",
                                "Looks at OC.",
                                "Opposed arc", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Opposed Satellite Arm",
                                "Hold 135\u00b0; take OC wrist.",
                                "Takes OC wrist.",
                                "Looks at Point.",
                                "Opposed arc", "Reacts on key"),
        }
    )

    # RANDOM P: SIDEBODY
    pool["P"] = FormationDefinition(
        code="P", name="Sidebody", is_block=False, points=1,
        initial_name="Sidebody",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="All sidebody grips locked (hand-to-hip/wrist); parallel headings",
        key_method="Visual nod from Inside Center",
        head_switch_summary="Centers look at each other; Point references Tail down the flank.",
        coach_tips=[
        "Standard exit formation from Twin Otter. Maintain close flank proximity.",
        "Flyers must fly side-by-side with zero yaw angle divergence."
],
        pitfalls_and_busts=[
        "Blowing apart laterally; one flyer banking away."
],
        state_initial={
            "Point": Flyer3DState(-10.1, 54.2, 0.0, 109.0, head_turn_deg=45, gaze_target="OC", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-22.5, 8.1, 0.0, 198.1, head_turn_deg=90, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(21.0, -8.3, 0.0, 104.1, head_turn_deg=-90, gaze_target="OC", left_grip="OC Right Wrist"),
            "Tail": Flyer3DState(11.5, -54.0, 0.0, 197.3, head_turn_deg=-45, gaze_target="IC", left_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Flank",
                                "Hold 0\u00b0 heading; lock right hand to OC wrist.",
                                "Takes OC wrist.",
                                "Head turned 45\u00b0 right to OC.",
                                "Flank alignment", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Left Flank",
                                "Hold 0\u00b0 heading; lock right hand to IC wrist.",
                                "Takes IC wrist.",
                                "Direct eye contact with IC.",
                                "Center alignment", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Right Flank & Keyer",
                                "Hold 0\u00b0 heading; lock left hand to OC wrist.",
                                "Takes OC wrist.",
                                "Direct eye contact with OC.",
                                "Center alignment", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Flank",
                                "Hold 0\u00b0 heading; lock left hand to IC wrist.",
                                "Takes IC wrist.",
                                "Head turned 45\u00b0 left to IC.",
                                "Flank alignment", "Reacts on key"),
        }
    )

    # RANDOM Q: PHALANX
    pool["Q"] = FormationDefinition(
        code="Q", name="Phalanx", is_block=False, points=1,
        initial_name="Phalanx",
        subgroup_split="",
        primary_key_slot="Inside Center",
        key_trigger="All 4 flyers aligned side-by-side in a straight horizontal line",
        key_method="Visual nod from Inside Center",
        head_switch_summary="All flyers look across the line; outer wings clone cross-reference each other.",
        coach_tips=[
        "Strict level matching across all 4 flyers; avoid bowing the phalanx."
],
        pitfalls_and_busts=[
        "Outer wings lagging behind or folding forward into a horseshoe."
],
        state_initial={
            "Point": Flyer3DState(-14.1, 49.2, 0.0, 100.0, head_turn_deg=60, gaze_target="Tail", right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-31.4, -4.2, 0.0, 110.8, head_turn_deg=45, gaze_target="IC", right_grip="IC Left Wrist"),
            "IC": Flyer3DState(30.8, 4.7, 0.0, 106.6, head_turn_deg=-45, gaze_target="OC", left_grip="OC Right Wrist"),
            "Tail": Flyer3DState(14.7, -49.7, 0.0, 109.4, head_turn_deg=-60, gaze_target="Point", left_grip="IC Right Wrist"),
        },
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Left End Phalanx",
                                "Align in line; match OC fall rate exactly.",
                                "Takes OC wrist.",
                                "Looks down line across to Tail.",
                                "Line alignment", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Center Left Phalanx",
                                "Maintain center line spacing.",
                                "Takes IC wrist; presents to Point.",
                                "Looks at IC and Point.",
                                "Line alignment", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Center Right Phalanx & Keyer",
                                "Anchor phalanx line; verify wings.",
                                "Takes OC wrist; presents to Tail.",
                                "Looks at OC and Tail.",
                                "Line anchor", "PRIMARY KEY"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Right End Phalanx",
                                "Align in line; match IC fall rate exactly.",
                                "Takes IC wrist.",
                                "Looks down line across to Point.",
                                "Line alignment", "Reacts on key"),
        }
    )

    # =========================================================================
    # 22 BLOCKS (1 through 22)
    # =========================================================================

    # BLOCK 1: MOLAR - MOLAR
    pool["1"] = FormationDefinition(
        code="1", name="Molar - Molar", is_block=True, points=2,
        initial_name="Molar",
        second_name="Molar",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Front 360\u00b0 / Rear 360\u00b0 (or 270\u00b0/90\u00b0)",
        primary_key_slot="Inside Center",
        key_trigger="Build 1: Molar built solid -> Key -> Break -> Inter -> Close Molar",
        key_method="Visual nod from Inside Center on Build 1; simultaneous closure on Build 2",
        head_switch_summary="During inter: Point head switches right to track IC; IC head switches left to track OC piece.",
        coach_tips=[
        "Vertical Technique: Front piece (Point + OC) generates slight lift to go over rear piece.",
        "Rear piece (IC + Tail) stays flat or slightly under in clean air.",
        "Piece partners must maintain firm, locked grip throughout the 360\u00b0 rotation."
],
        pitfalls_and_busts=[
        "Piece partners breaking grip during inter rotation; front piece funneling into rear piece burble."
],
        state_initial={
            "Point": Flyer3DState(-9.6, 39.8, 0.0, 129.9, right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-38.6, 5.2, 0.0, 226.2, left_grip="Point Right Wrist"),
            "IC": Flyer3DState(39.3, -5.3, 0.0, 131.5, right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(8.8, -39.7, 0.0, 221.7, left_grip="IC Right Wrist"),
        },
        state_close={
            "Point": Flyer3DState(-9.9, 39.2, 0.0, 126.8, right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-37.7, 2.9, 0.0, 222.4, left_grip="Point Right Wrist"),
            "IC": Flyer3DState(38.2, -3.5, 0.0, 128.6, right_grip="Tail Left Wrist"),
            "Tail": Flyer3DState(9.4, -38.6, 0.0, 223.1, left_grip="IC Right Wrist"),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Front Piece Outside Flyer",
                                "Spin 2-way with OC 360\u00b0; fly over in vertical.",
                                "Locks grip with OC.",
                                "Head switch to spot rear piece at 180\u00b0 inter.",
                                "360\u00b0 Piece Spin", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Front Piece Inside Pivot",
                                "Control piece radius; match Point fall rate.",
                                "Locks grip with Point.",
                                "Maintains focus on Point.",
                                "360\u00b0 Piece Spin", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Rear Piece Inside Pivot & Keyer",
                                "Key Build 1; rotate rear piece 360\u00b0 with Tail.",
                                "Locks grip with Tail.",
                                "Head switch left to spot closing front piece.",
                                "360\u00b0 Piece Spin", "PRIMARY KEY Build 1"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Rear Piece Outside Flyer",
                                "Drive rear piece rotation with strong legs.",
                                "Locks grip with IC.",
                                "Focus on IC and closing target.",
                                "360\u00b0 Piece Spin", "Assists close"),
        }
    )

    # BLOCK 2: SIDEBODY DONUT - SIDEFLAKE DONUT
    pool["2"] = FormationDefinition(
        code="2", name="Sidebody Donut - Sideflake Donut", is_block=True, points=2,
        initial_name="Sidebody Donut",
        second_name="Sideflake Donut",
        subgroup_split="3-Way (OC + IC + Tail) / Solo (Point)",
        inter_degrees="3-Way 360\u00b0 Spin / Solo Translation",
        primary_key_slot="Point",
        key_trigger="Sidebody Donut locked -> Point keys -> 3-Way turns 360\u00b0 while Point translates -> Rebuild Sideflake Donut",
        key_method="Visual Nod / Flash",
        head_switch_summary="Point cross-references 3-way center during translation; 3-way maintains tight donut axis throughout 360\u00b0 turn.",
        coach_tips=[
        "Point must release cleanly and translate down the line without drifting wide.",
        "3-way must turn smoothly as a rigid unit without deforming the donut shape."
],
        pitfalls_and_busts=[
        "3-way funneling or expanding radius during 360\u00b0 spin.",
        "Point arriving late at closing sideflake."
],
        state_initial={
            "Point": Flyer3DState(-4.8, 53.6, 0.0, 290.2),
            "OC": Flyer3DState(0.2, 10.3, 0.0, 272.0),
            "IC": Flyer3DState(26.3, -29.1, 0.0, 35.7),
            "Tail": Flyer3DState(-21.7, -34.8, 0.0, 160.8),
        },
        state_close={
            "Point": Flyer3DState(44.8, 1.3, 0.0, 178.3, head_turn_deg=-20),
            "OC": Flyer3DState(11.6, 3.8, 0.0, 137.9),
            "IC": Flyer3DState(-25.2, -26.4, 0.0, 124.4),
            "Tail": Flyer3DState(-31.2, 21.3, 0.0, 248.7),
        },
        pieces=[PieceKinematics(['OC', 'IC', 'Tail'], 360.0, 'center', 0.0), PieceKinematics(['Point'], 360.0, 'center', 0.0)],
    )

    # BLOCK 3: SIDEFLAKE OPAL - TURF
    pool["3"] = FormationDefinition(
        code="3", name="Sideflake Opal - Turf", is_block=True, points=2,
        initial_name="Sideflake Opal",
        second_name="Turf",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Translation + 180\u00b0 rotation",
        primary_key_slot="Inside Center",
        key_trigger="Sideflake Opal complete -> Key -> Cross center -> Turf",
        key_method="Visual Nod / Flash",
        head_switch_summary="Both centers head switch across center to monitor crossing paths.",
        coach_tips=[
        "Crossover requires strict Start-Coast-Stop momentum management."
],
        pitfalls_and_busts=[
        "Collision during center crossover; overshooting the Turf build."
],
        state_initial={
            "Point": Flyer3DState(0.8, 35.3, 0.0, 269.7),
            "OC": Flyer3DState(-32.1, -2.5, 0.0, 118.4),
            "IC": Flyer3DState(14.3, 8.8, 0.0, 100.4),
            "Tail": Flyer3DState(17.1, -41.6, 0.0, 155.0),
        },
        state_close={
            "Point": Flyer3DState(-3.6, 42.0, 0.0, 102.3),
            "OC": Flyer3DState(27.0, 0.2, 0.0, 213.7),
            "IC": Flyer3DState(2.5, -44.1, 0.0, 270.3),
            "Tail": Flyer3DState(-25.9, 1.9, 0.0, 309.6),
        },
        pieces=[PieceKinematics(['Point', 'IC'], 540.0, 'center', 0.0), PieceKinematics(['OC', 'Tail'], 180.0, 'center', 0.0)],
    )

    # BLOCK 4: MONOPOD - MONOPOD
    pool["4"] = FormationDefinition(
        code="4", name="Monopod - Monopod", is_block=True, points=2,
        initial_name="Monopod",
        second_name="Monopod",
        subgroup_split="Solo (Point) + 3-Way (OC, IC, Tail)",
        inter_degrees="3-Way rotates 360\u00b0; Point rotates 360\u00b0 solo",
        primary_key_slot="Inside Center",
        key_trigger="Monopod built -> Key -> 360\u00b0 spins -> Rebuild Monopod",
        key_method="Visual Nod / Flash",
        head_switch_summary="Point head switches to track 3-way rotation; IC monitors Point's arrival.",
        coach_tips=[
        "Point does an isolated in-place 360\u00b0 turn; 3-way rotates as a tight, unified piece."
],
        pitfalls_and_busts=[
        "Point carving wide away from the 3-way; 3-way piece breaking apart."
],
        state_initial={
            "Point": Flyer3DState(-3.5, 61.0, 0.0, 233.0),
            "OC": Flyer3DState(-21.2, 12.7, 0.0, 133.2),
            "IC": Flyer3DState(30.4, -18.9, 0.0, 81.3),
            "Tail": Flyer3DState(-5.7, -54.9, 0.0, 342.1),
        },
        state_close={
            "Point": Flyer3DState(63.4, 19.8, 0.0, 228.1),
            "OC": Flyer3DState(8.8, 3.8, 0.0, 292.2),
            "IC": Flyer3DState(-24.3, -39.6, 0.0, 179.4),
            "Tail": Flyer3DState(-47.9, 16.0, 0.0, 304.9),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
    )

    # BLOCK 5: OPAL - OPAL
    pool["5"] = FormationDefinition(
        code="5", name="Opal - Opal", is_block=True, points=2,
        initial_name="Opal",
        second_name="Opal",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Opposing 360\u00b0 spins",
        primary_key_slot="Inside Center",
        key_trigger="Opal built solid -> Key -> 360\u00b0 spins -> Rebuild Opal",
        key_method="Visual Nod / Flash",
        head_switch_summary="Each piece head switches inward at 180\u00b0 to calibrate closing distance.",
        coach_tips=[
        "Vertical option allows pieces to rotate closer together without wingtips touching."
],
        pitfalls_and_busts=[
        "Pieces drifting apart during the 360\u00b0 spin."
],
        state_initial={
            "Point": Flyer3DState(-7.1, 35.2, 0.0, 154.7),
            "OC": Flyer3DState(-39.2, -2.9, 0.0, 120.6),
            "IC": Flyer3DState(36.0, 4.7, 0.0, 121.5),
            "Tail": Flyer3DState(10.4, -37.0, 0.0, 270.6),
        },
        state_close={
            "Point": Flyer3DState(-5.2, 40.9, 0.0, 102.5),
            "OC": Flyer3DState(37.0, 6.9, 0.0, 179.4),
            "IC": Flyer3DState(-35.4, -11.9, 0.0, 63.7),
            "Tail": Flyer3DState(3.7, -35.9, 0.0, 143.1),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    # BLOCK 6: STARDIAN - STARDIAN
    pool["6"] = FormationDefinition(
        code="6", name="Stardian - Stardian", is_block=True, points=2,
        initial_name="Stardian",
        second_name="Stardian",
        supports_vertical=True,
        subgroup_split="2-Way / 2-Way",
        inter_degrees="180\u00b0 rotation",
        primary_key_slot="Inside Center",
        key_trigger="Stardian build -> Key -> 180\u00b0 inter -> Close Stardian",
        key_method="Visual Nod / Flash",
        head_switch_summary="Wings head switch across center; Centers keep focus on inter picture.",
        coach_tips=[
        "Vertical technique has front piece pop slightly over rear piece."
],
        pitfalls_and_busts=[
        "Under-rotating the 180\u00b0; failing to achieve clear separation."
],
        state_initial={
            "Point": Flyer3DState(2.9, 32.2, 0.0, 93.3),
            "OC": Flyer3DState(-45.1, 4.2, 0.0, 122.5),
            "IC": Flyer3DState(40.7, 4.5, 0.0, 111.2),
            "Tail": Flyer3DState(1.5, -40.9, 0.0, 181.1),
        },
        state_close={
            "Point": Flyer3DState(-24.1, -21.1, 0.0, 153.6),
            "OC": Flyer3DState(19.5, -36.3, 0.0, 134.7),
            "IC": Flyer3DState(-29.1, 36.3, 0.0, 123.4),
            "Tail": Flyer3DState(33.7, 21.1, 0.0, 49.6),
        },
        state_close_vertical={
            "Point": Flyer3DState(-0.4, -34.2, 0.0, 273.4),
            "OC": Flyer3DState(45.5, -3.4, 0.0, 88.6),
            "IC": Flyer3DState(-46.4, -1.2, 0.0, 122.2),
            "Tail": Flyer3DState(1.3, 38.8, 0.0, 359.7),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    # BLOCK 7: SIDEBUDDIES - SIDEBUDDIES
    pool["7"] = FormationDefinition(
        code="7", name="Sidebuddies - Sidebuddies", is_block=True, points=2,
        initial_name="Sidebuddies",
        second_name="Sidebuddies",
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="360\u00b0 Opposed Spins",
        primary_key_slot="Inside Center",
        key_trigger="Sidebuddies built -> Key -> 360\u00b0 spins -> Rebuild Sidebuddies",
        key_method="Visual Nod / Flash",
        head_switch_summary="At 180\u00b0, centers head switch across center to calibrate stop timing.",
        coach_tips=[
        "Pieces must turn on their own geometric centerpoints without drifting laterally."
],
        pitfalls_and_busts=[
        "Pieces expanding outward, requiring a long closing reach."
],
        state_initial={
            "Point": Flyer3DState(-9.6, 38.4, 0.0, 95.2),
            "OC": Flyer3DState(-37.6, 2.5, 0.0, 314.8),
            "IC": Flyer3DState(41.1, -5.7, 0.0, 135.3),
            "Tail": Flyer3DState(6.1, -35.2, 0.0, 131.4),
        },
        state_close={
            "Point": Flyer3DState(-9.6, 38.4, 0.0, 95.2),
            "OC": Flyer3DState(-37.6, 2.5, 0.0, 314.8),
            "IC": Flyer3DState(41.1, -5.7, 0.0, 135.3),
            "Tail": Flyer3DState(6.1, -35.2, 0.0, 131.4),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
    )

    # BLOCK 8: CANADIAN TEE - CANADIAN TEE
    pool["8"] = FormationDefinition(
        code="8", name="Canadian Tee - Canadian Tee", is_block=True, points=2,
        initial_name="Canadian Tee",
        second_name="Canadian Tee",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Front piece translates over rear piece",
        primary_key_slot="Inside Center",
        key_trigger="Canadian Tee build -> Key -> Front piece slides over rear -> Rebuild",
        key_method="Visual Nod / Flash",
        head_switch_summary="Point and OC look down as they cross over; IC and Tail look up through burble.",
        coach_tips=[
        "Monopod-like intermediate picture must be achieved cleanly."
],
        pitfalls_and_busts=[
        "Front piece dropping onto rear piece (burble collision)."
],
        state_initial={
            "Point": Flyer3DState(13.5, 47.8, 0.0, 135.6),
            "OC": Flyer3DState(-24.2, 28.3, 0.0, 172.7),
            "IC": Flyer3DState(8.5, -8.2, 0.0, 130.5),
            "Tail": Flyer3DState(2.1, -67.9, 0.0, 38.0),
        },
        state_close={
            "Point": Flyer3DState(14.3, 46.1, 0.0, 144.0),
            "OC": Flyer3DState(-26.2, 31.8, 0.0, 180.7),
            "IC": Flyer3DState(3.4, -8.3, 0.0, 130.5),
            "Tail": Flyer3DState(8.5, -69.6, 0.0, 15.9),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 180.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 180.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 180.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 180.0, 'center', -16.0)],
    )

    # BLOCK 9: CAT + ACCORDION - CAT + ACCORDION
    pool["9"] = FormationDefinition(
        code="9", name="Cat + Accordion - Cat + Accordion", is_block=True, points=2,
        initial_name="Cat + Accordion",
        second_name="Cat + Accordion",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Subgroups swap positions across center",
        primary_key_slot="Inside Center",
        key_trigger="Cat + Accordion built -> Key -> Subgroups swap -> Rebuild",
        key_method="Visual Nod / Flash",
        head_switch_summary="Tail head switches to watch cat connection swap.",
        coach_tips=[
        "Subgroups must maintain internal cohesion while swapping positions."
],
        pitfalls_and_busts=[
        "Pieces crossing too close and colliding."
],
        state_initial={
            "Point": Flyer3DState(-9.9, 30.3, 0.0, 133.2),
            "OC": Flyer3DState(-32.1, 9.3, 0.0, 311.0),
            "IC": Flyer3DState(36.6, 1.0, 0.0, 215.4),
            "Tail": Flyer3DState(5.5, -40.6, 0.0, 218.0),
        },
        state_close={
            "Point": Flyer3DState(-14.5, 32.5, 0.0, 298.4),
            "OC": Flyer3DState(-29.9, 6.0, 0.0, 131.4),
            "IC": Flyer3DState(38.5, 2.9, 0.0, 217.1),
            "Tail": Flyer3DState(5.9, -41.4, 0.0, 38.6),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 180.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 180.0, 'center', 0.0)],
    )

    # BLOCK 10: DIAMOND - BUNYIP
    pool["10"] = FormationDefinition(
        code="10", name="Diamond - Bunyip", is_block=True, points=2,
        initial_name="Diamond",
        second_name="Bunyip",
        subgroup_split="Pieces break; rotate into Bunyip",
        inter_degrees="180\u00b0 / 360\u00b0",
        primary_key_slot="Inside Center",
        key_trigger="Diamond built -> Key -> Break and rotate -> Close Bunyip",
        key_method="Visual Nod / Flash",
        head_switch_summary="Wings head switch inward as centers drive the Bunyip shape.",
        coach_tips=[
        "Diamond must break cleanly; all 4 flyers maintain planar trim."
],
        pitfalls_and_busts=[
        "Premature Bunyip grip before complete Diamond separation."
],
        state_initial={
            "Point": Flyer3DState(-6.4, 49.2, 0.0, 153.0),
            "OC": Flyer3DState(-26.9, -0.4, 0.0, 181.8),
            "IC": Flyer3DState(32.5, -0.4, 0.0, 175.6),
            "Tail": Flyer3DState(0.8, -48.5, 0.0, 144.3),
        },
        state_close={
            "Point": Flyer3DState(-29.6, -23.1, 0.0, 1.5),
            "OC": Flyer3DState(1.0, 24.8, 0.0, 181.6),
            "IC": Flyer3DState(31.1, 22.1, 0.0, 179.2),
            "Tail": Flyer3DState(-2.5, -23.8, 0.0, 137.6),
        },
        pieces=[PieceKinematics(['Point', 'Tail'], 360.0, 'center', 0.0), PieceKinematics(['OC', 'IC'], 180.0, 'center', 0.0)],
    )

    # BLOCK 11: PHOTON - PHOTON
    pool["11"] = FormationDefinition(
        code="11", name="Photon - Photon", is_block=True, points=2,
        initial_name="Photon",
        second_name="Photon",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="180\u00b0 / 360\u00b0 Vertical Crossover",
        primary_key_slot="Inside Center",
        key_trigger="Photon built -> Key -> Vertical crossover -> Rebuild Photon",
        key_method="Visual Nod / Flash",
        head_switch_summary="Tail goes under Point and anchors in '2-way star'; IC waits for star target, head switches down.",
        coach_tips=[
        "Tail goes under Point and anchors in the '2-way star' with Point.",
        "IC waits for the '2-way star' target and performs the same task.",
        "Point focuses on IC's gripping hand to close as fast as possible."
],
        pitfalls_and_busts=[
        "Tail floating into Point's burble; Point snatching grip before IC is set."
],
        state_initial={
            "Point": Flyer3DState(-14.6, 24.9, 0.0, 133.9),
            "OC": Flyer3DState(-35.4, 3.0, 0.0, 310.7),
            "IC": Flyer3DState(39.7, 6.7, 0.0, 108.5),
            "Tail": Flyer3DState(10.4, -34.5, 0.0, 257.3),
        },
        state_close={
            "Point": Flyer3DState(-26.9, -13.4, 0.0, 45.6),
            "OC": Flyer3DState(-11.9, -31.8, 0.0, 315.1),
            "IC": Flyer3DState(4.2, 45.8, 0.0, 129.0),
            "Tail": Flyer3DState(34.6, -0.6, 0.0, 170.9),
        },
        state_close_vertical={
            "Point": Flyer3DState(-22.3, -16.4, 0.0, 42.4),
            "OC": Flyer3DState(-4.4, -33.8, 0.0, 317.4),
            "IC": Flyer3DState(-6.1, 44.5, 0.0, 126.0),
            "Tail": Flyer3DState(32.9, 5.8, 0.0, 161.5),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    # BLOCK 12: BUNDY - BUNDY
    pool["12"] = FormationDefinition(
        code="12", name="Bundy - Bundy", is_block=True, points=2,
        initial_name="Bundy",
        second_name="Bundy",
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Front Piece 540\u00b0 / Rear Piece 360\u00b0",
        primary_key_slot="Inside Center",
        key_trigger="Bundy built in line -> IC keys -> Front piece turns 540\u00b0, Rear piece turns 360\u00b0 -> Rebuild perpendicular Bundy",
        key_method="Visual Nod / Flash",
        head_switch_summary="Centers cross-reference across center during simultaneous 540\u00b0/360\u00b0 turns.",
        coach_tips=[
        "Front piece (Point + OC) executes explosive 540\u00b0 carve maintaining tight piece axis.",
        "Rear piece (IC + Tail) executes compact 360\u00b0 spin in place.",
        "Both pieces must match fall rate and close on the perpendicular axis."
],
        pitfalls_and_busts=[
        "Front piece blowing out wide during 540\u00b0 rotation.",
        "Rear piece over-rotating past 360\u00b0."
],
        state_initial={
            "Point": Flyer3DState(3.4, 43.2, 0.0, 91.5),
            "OC": Flyer3DState(2.7, 14.7, 0.0, 274.3),
            "IC": Flyer3DState(-9.0, -5.9, 0.0, 304.9),
            "Tail": Flyer3DState(2.9, -51.9, 0.0, 179.8),
        },
        state_close={
            "Point": Flyer3DState(13.4, 3.2, 0.0, 291.9),
            "OC": Flyer3DState(46.4, -1.5, 0.0, 181.0),
            "IC": Flyer3DState(-10.2, 0.9, 0.0, 129.4),
            "Tail": Flyer3DState(-49.5, -2.5, 0.0, 269.1),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 540.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
    )

    # BLOCK 13: MIXED ACCORDION - MIXED ACCORDION
    pool["13"] = FormationDefinition(
        code="13", name="Mixed Accordion - Mixed Accordion", is_block=True, points=2,
        initial_name="Mixed Accordion",
        second_name="Mixed Accordion",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Reverse direction & rebuild",
        primary_key_slot="Inside Center",
        key_trigger="Mixed Accordion built -> Key -> Break, reverse, rebuild",
        key_method="Visual Nod / Flash",
        head_switch_summary="Centers hold head switch to guarantee clean inter picture.",
        coach_tips=[
        "Hold the head switch in the inter picture before closing."
],
        pitfalls_and_busts=[
        "Rushing the close before completing the reverse move."
],
        state_initial={
            "Point": Flyer3DState(2.8, 55.8, 0.0, 352.0),
            "OC": Flyer3DState(-1.6, 13.7, 0.0, 108.2),
            "IC": Flyer3DState(-4.7, -11.2, 0.0, 305.1),
            "Tail": Flyer3DState(3.5, -58.2, 0.0, 170.1),
        },
        state_close={
            "Point": Flyer3DState(54.9, 7.3, 0.0, 145.1),
            "OC": Flyer3DState(-2.6, 13.6, 0.0, 110.4),
            "IC": Flyer3DState(-5.8, -10.8, 0.0, 306.2),
            "Tail": Flyer3DState(-46.5, -10.1, 0.0, 330.9),
        },
        state_close_vertical={
            "Point": Flyer3DState(45.6, -32.9, 0.0, 191.5),
            "OC": Flyer3DState(5.8, 9.9, 0.0, 299.0),
            "IC": Flyer3DState(-15.1, -5.7, 0.0, 132.6),
            "Tail": Flyer3DState(-36.3, 28.7, 0.0, 16.5),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    # BLOCK 14: BIPOLE - BIPOLE
    pool["14"] = FormationDefinition(
        code="14", name="Bipole - Bipole", is_block=True, points=2,
        initial_name="Bipole",
        second_name="Bipole",
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="360\u00b0 opposing spins",
        primary_key_slot="Inside Center",
        key_trigger="Bipole built -> Key -> 360\u00b0 piece spins -> Rebuild Bipole",
        key_method="Visual Nod / Flash",
        head_switch_summary="At 180\u00b0, both pieces head switch inward to set closing line.",
        coach_tips=[
        "Piece partners must maintain identical fall rate during high-speed spin."
],
        pitfalls_and_busts=[
        "Pieces expanding outward; asymmetric piece spin speed."
],
        state_initial={
            "Point": Flyer3DState(-2.7, 43.5, 0.0, 297.3),
            "OC": Flyer3DState(-37.0, -1.5, 0.0, 81.6),
            "IC": Flyer3DState(40.8, -0.8, 0.0, 261.3),
            "Tail": Flyer3DState(-1.2, -41.2, 0.0, 143.1),
        },
        state_close={
            "Point": Flyer3DState(-0.1, 39.7, 0.0, 170.1),
            "OC": Flyer3DState(-40.8, 1.0, 0.0, 123.7),
            "IC": Flyer3DState(36.6, 2.4, 0.0, 111.7),
            "Tail": Flyer3DState(4.2, -43.1, 0.0, 349.8),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 540.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 540.0, 'center', 0.0)],
    )

    # BLOCK 15: CATERPILLAR - CATERPILLAR
    pool["15"] = FormationDefinition(
        code="15", name="Caterpillar - Caterpillar", is_block=True, points=2,
        initial_name="Caterpillar",
        second_name="Caterpillar",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Translation into linear caterpillar",
        primary_key_slot="Inside Center",
        key_trigger="Caterpillar built -> Key -> Translate -> Rebuild Caterpillar",
        key_method="Visual Nod / Flash",
        head_switch_summary="Tail looks along the line of flight to guide rear docking.",
        coach_tips=[
        "Maintain linear alignment; do not allow the caterpillar to buckle."
],
        pitfalls_and_busts=[
        "Buckling in the middle; hard docking."
],
        state_initial={
            "Point": Flyer3DState(0.4, 34.8, 0.0, 100.1),
            "OC": Flyer3DState(-40.6, 15.3, 0.0, 36.4),
            "IC": Flyer3DState(24.6, -1.6, 0.0, 123.1),
            "Tail": Flyer3DState(15.6, -48.4, 0.0, 44.6),
        },
        state_close={
            "Point": Flyer3DState(0.4, 34.8, 0.0, 100.1),
            "OC": Flyer3DState(-40.6, 15.3, 0.0, 36.4),
            "IC": Flyer3DState(24.6, -1.6, 0.0, 123.1),
            "Tail": Flyer3DState(15.6, -48.4, 0.0, 44.6),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
    )

    # BLOCK 16: COMPRESSED ACCORDION - BOX
    pool["16"] = FormationDefinition(
        code="16", name="Compressed Accordion - Box", is_block=True, points=2,
        initial_name="Compressed Accordion",
        second_name="Box",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="180\u00b0 rotation into open Box",
        primary_key_slot="Inside Center",
        key_trigger="Compressed built -> Key -> 180\u00b0 rotation -> Close Box",
        key_method="Visual Nod / Flash",
        head_switch_summary="Centers head switch across box as pieces open up.",
        coach_tips=[
        "Centers must control width so the Box does not open too wide."
],
        pitfalls_and_busts=[
        "Over-opening the Box; missing wrist grips."
],
        state_initial={
            "Point": Flyer3DState(1.6, 43.2, 0.0, 92.3),
            "OC": Flyer3DState(-1.9, 14.4, 0.0, 266.6),
            "IC": Flyer3DState(-2.7, -11.6, 0.0, 121.5),
            "Tail": Flyer3DState(3.1, -46.0, 0.0, 270.1),
        },
        state_close={
            "Point": Flyer3DState(-16.1, 34.1, 0.0, 143.2),
            "OC": Flyer3DState(17.1, 30.2, 0.0, 181.3),
            "IC": Flyer3DState(13.0, -29.1, 0.0, 144.8),
            "Tail": Flyer3DState(-13.9, -35.2, 0.0, 359.5),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 270.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 270.0, 'center', 0.0)],
    )

    # BLOCK 17: DANISH TEE - MURPHY
    pool["17"] = FormationDefinition(
        code="17", name="Danish Tee - Murphy", is_block=True, points=2,
        initial_name="Danish Tee",
        second_name="Murphy",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="Translation across center",
        primary_key_slot="Inside Center",
        key_trigger="Danish Tee built -> Key -> Cross center -> Close Murphy",
        key_method="Visual Nod / Flash",
        head_switch_summary="Both pieces head switch across center to spot Murphy alignment.",
        coach_tips=[
        "Smooth translation into a clean, planar Murphy Flake."
],
        pitfalls_and_busts=[
        "Over-sliding past the Murphy line."
],
        state_initial={
            "Point": Flyer3DState(-10.6, 27.6, 0.0, 88.5),
            "OC": Flyer3DState(-14.4, -0.9, 0.0, 92.3),
            "IC": Flyer3DState(37.5, 3.0, 0.0, 111.0),
            "Tail": Flyer3DState(-12.5, -29.7, 0.0, 89.7),
        },
        state_close={
            "Point": Flyer3DState(-30.1, 32.8, 0.0, 318.3),
            "OC": Flyer3DState(37.2, 27.3, 0.0, 234.4),
            "IC": Flyer3DState(-37.0, -25.0, 0.0, 140.5),
            "Tail": Flyer3DState(29.9, -35.2, 0.0, 141.8),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
    )

    # BLOCK 18: ZIRCON - ZIRCON
    pool["18"] = FormationDefinition(
        code="18", name="Zircon - Zircon", is_block=True, points=2,
        initial_name="Zircon",
        second_name="Zircon",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="180\u00b0 crossover",
        primary_key_slot="Inside Center",
        key_trigger="Zircon built -> Key -> 180\u00b0 crossover -> Rebuild Zircon",
        key_method="Visual Nod / Flash",
        head_switch_summary="Vertical: Over piece head switches down; Under piece head switches up.",
        coach_tips=[
        "Vertical crossover allows pieces to cross paths without blowing out."
],
        pitfalls_and_busts=[
        "Collision during crossover; incorrect angle on close."
],
        state_initial={
            "Point": Flyer3DState(-10.8, -5.6, 0.0, 188.2),
            "OC": Flyer3DState(-8.9, 20.0, 0.0, 10.9),
            "IC": Flyer3DState(15.6, 13.0, 0.0, 15.5),
            "Tail": Flyer3DState(4.2, -27.4, 0.0, 143.8),
        },
        state_close={
            "Point": Flyer3DState(-3.5, 45.2, 0.0, 275.5),
            "OC": Flyer3DState(-11.4, 3.0, 0.0, 10.9),
            "IC": Flyer3DState(13.1, -3.9, 0.0, 15.5),
            "Tail": Flyer3DState(1.8, -44.3, 0.0, 143.8),
        },
        state_close_vertical={
            "Point": Flyer3DState(-44.7, -32.5, 0.0, 323.3),
            "OC": Flyer3DState(8.5, -17.2, 0.0, 242.0),
            "IC": Flyer3DState(-3.6, 12.2, 0.0, 245.2),
            "Tail": Flyer3DState(39.8, 37.4, 0.0, 93.2),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    # BLOCK 19: RITZ - ICE PICK
    pool["19"] = FormationDefinition(
        code="19", name="Ritz - Ice Pick", is_block=True, points=2,
        initial_name="Ritz",
        second_name="Ice Pick",
        subgroup_split="2-Way / 2-Way",
        inter_degrees="180\u00b0 spin to Ice Pick",
        primary_key_slot="Inside Center",
        key_trigger="Ritz built -> Key -> 180\u00b0 rotation -> Close Ice Pick",
        key_method="Visual Nod / Flash",
        head_switch_summary="Centers head switch across center to verify Ice Pick shape.",
        coach_tips=[
        "Ice Pick requires precise grip presentation from wings."
],
        pitfalls_and_busts=[
        "Missing the Ice Pick wrist grips; level mismatch."
],
        state_initial={
            "Point": Flyer3DState(-4.4, 52.3, 0.0, 21.3),
            "OC": Flyer3DState(-22.6, 1.7, 0.0, 11.3),
            "IC": Flyer3DState(13.7, -4.0, 0.0, 118.3),
            "Tail": Flyer3DState(13.3, -50.0, 0.0, 195.8),
        },
        state_close={
            "Point": Flyer3DState(-65.8, 9.1, 0.0, 271.2),
            "OC": Flyer3DState(-12.9, 8.6, 0.0, 265.0),
            "IC": Flyer3DState(34.8, 14.8, 0.0, 112.5),
            "Tail": Flyer3DState(43.9, -32.5, 0.0, 174.6),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 270.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
    )

    # BLOCK 20: PIVER - VIPER
    pool["20"] = FormationDefinition(
        code="20", name="Piver - Viper", is_block=True, points=2,
        initial_name="Piver",
        second_name="Viper",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Rotate and translate across center",
        primary_key_slot="Inside Center",
        key_trigger="Piver built -> Key -> Cross center -> Close Viper",
        key_method="Visual Nod / Flash",
        head_switch_summary="Wings head switch across center; Centers keep focus on piece line.",
        coach_tips=[
        "Vertical option allows smooth over/under crossover without wide bows."
],
        pitfalls_and_busts=[
        "Overshooting Viper build; failing to stop momentum."
],
        state_initial={
            "Point": Flyer3DState(0.2, 41.8, 0.0, 111.7),
            "OC": Flyer3DState(-33.4, 4.0, 0.0, 179.3),
            "IC": Flyer3DState(36.9, -6.1, 0.0, 118.1),
            "Tail": Flyer3DState(-3.6, -39.8, 0.0, 182.5),
        },
        state_close={
            "Point": Flyer3DState(-41.0, 2.6, 0.0, 20.8),
            "OC": Flyer3DState(-6.7, -35.2, 0.0, 86.4),
            "IC": Flyer3DState(6.5, 37.1, 0.0, 27.1),
            "Tail": Flyer3DState(41.2, -4.4, 0.0, 88.6),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    # BLOCK 21: ZIG ZAG - MARQUIS
    pool["21"] = FormationDefinition(
        code="21", name="Zig Zag - Marquis", is_block=True, points=2,
        initial_name="Zig Zag",
        second_name="Marquis",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="Centers step out; wings cross over with 180\u00b0 turns",
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
            "Point": Flyer3DState(-21.3, 44.2, 0.0, 356.2, right_grip="OC Left Wrist"),
            "OC": Flyer3DState(-26.5, 7.5, 0.0, 299.1, left_grip="IC Left Wrist"),
            "IC": Flyer3DState(22.8, -4.4, 0.0, 297.2, right_grip="OC Right Wrist"),
            "Tail": Flyer3DState(25.0, -47.3, 0.0, 175.9, left_grip="IC Right Wrist"),
        },
        state_close={
            "Point": Flyer3DState(54.0, 26.0, 0.0, 62.4, right_grip="IC Left Wrist"),
            "OC": Flyer3DState(9.7, 7.7, 0.0, 122.4, left_grip="Point Left Wrist"),
            "IC": Flyer3DState(-15.8, -3.4, 0.0, 133.4, right_grip="Tail Right Wrist"),
            "Tail": Flyer3DState(-47.9, -30.3, 0.0, 240.0, left_grip="OC Right Wrist"),
        },
        state_close_vertical={
            "Point": Flyer3DState(54.0, 26.0, 0.0, 62.4),
            "OC": Flyer3DState(9.7, 7.7, 0.0, 122.4),
            "IC": Flyer3DState(-15.8, -3.4, 0.0, 133.4),
            "Tail": Flyer3DState(-47.9, -30.3, 0.0, 240.0),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 360.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
        slot_details={
            "Point": SlotDetail("Point", COLOR_POINT, "Over Piece Wing",
                                "Cross over under piece; rotate 180\u00b0 into Marquis.",
                                "Takes IC wrist on close.",
                                "Head switch down to spot IC during crossover.",
                                "180\u00b0 Crossover", "Reacts on key"),
            "OC": SlotDetail("Outside Center", COLOR_OC, "Over Piece Center",
                                "Step out at angle; STOP outward momentum as Point crosses.",
                                "Connects with Point.",
                                "Looks down and across at Tail.",
                                "Step out & brake", "Assists key"),
            "IC": SlotDetail("Inside Center", COLOR_IC, "Under Piece Center & Keyer",
                                "Key Build 1; step out low; STOP outward drift as Tail crosses.",
                                "Connects with Tail.",
                                "Looks up and across at OC.",
                                "Step out & brake", "PRIMARY KEY Build 1"),
            "Tail": SlotDetail("Tail", COLOR_TAIL, "Under Piece Wing",
                                "Drive under front piece; rotate 180\u00b0 into Marquis.",
                                "Takes OC wrist on close.",
                                "Head switch up to spot Point during crossover.",
                                "180\u00b0 Crossover", "Reacts on close"),
        }
    )

    # BLOCK 22: TEE - CHINESE TEE
    pool["22"] = FormationDefinition(
        code="22", name="Tee - Chinese Tee", is_block=True, points=2,
        initial_name="Tee",
        second_name="Chinese Tee",
        supports_vertical=True,
        subgroup_split="2-Way (Point + OC) / 2-Way (IC + Tail)",
        inter_degrees="180\u00b0 crossover",
        primary_key_slot="Inside Center",
        key_trigger="Tee built -> Key -> 180\u00b0 crossover -> Close Chinese Tee",
        key_method="Visual Nod / Flash",
        head_switch_summary="Front piece head switches down; rear piece head switches up during 180\u00b0 rotation.",
        coach_tips=[
        "Evaluate build axis vs previous formation center.",
        "Front piece pops slightly; rear piece stays flat underneath."
],
        pitfalls_and_busts=[
        "Front piece hitting rear piece burble; over-rotating."
],
        state_initial={
            "Point": Flyer3DState(-24.5, -21.5, 0.0, 357.5),
            "OC": Flyer3DState(-5.7, 12.9, 0.0, 186.7),
            "IC": Flyer3DState(40.0, -22.5, 0.0, 172.5),
            "Tail": Flyer3DState(-9.9, 31.1, 0.0, 197.2),
        },
        state_close={
            "Point": Flyer3DState(-16.8, 16.5, 0.0, 16.8),
            "OC": Flyer3DState(0.4, 9.6, 0.0, 300.2),
            "IC": Flyer3DState(24.2, 4.6, 0.0, 16.8),
            "Tail": Flyer3DState(-7.8, -30.7, 0.0, 197.0),
        },
        state_close_vertical={
            "Point": Flyer3DState(-18.8, 18.5, 0.0, 17.4),
            "OC": Flyer3DState(0.1, 11.0, 0.0, 299.9),
            "IC": Flyer3DState(27.5, 5.4, 0.0, 17.2),
            "Tail": Flyer3DState(-8.9, -34.9, 0.0, 196.3),
        },
        pieces=[PieceKinematics(['Point', 'OC'], 270.0, 'center', 0.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', 0.0)],
        pieces_vertical=[PieceKinematics(['Point', 'OC'], 270.0, 'center', 16.0), PieceKinematics(['IC', 'Tail'], 360.0, 'center', -16.0)],
    )

    return pool


# Global Singleton Dive Pool
DIVE_POOL: Dict[str, FormationDefinition] = _build_dive_pool()


def get_formation(code: str) -> Optional[FormationDefinition]:
    """Fetches formation definition by code ('A'..'Q', or '1'..'22')."""
    return DIVE_POOL.get(code.upper().strip())


def get_all_formations() -> List[FormationDefinition]:
    """Returns all formations sorted by category and code."""
    randoms = [f for f in DIVE_POOL.values() if not f.is_block]
    blocks = [f for f in DIVE_POOL.values() if f.is_block]
    randoms.sort(key=lambda f: f.code)
    blocks.sort(key=lambda f: int(f.code) if f.code.isdigit() else 999)
    return randoms + blocks


def get_all_randoms() -> List[FormationDefinition]:
    return [f for f in get_all_formations() if not f.is_block]


def get_all_blocks() -> List[FormationDefinition]:
    return [f for f in get_all_formations() if f.is_block]
