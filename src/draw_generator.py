"""
FAI 4-Way Formation Skydiving Draw Generator.
Generates competition and training draws adhering to official FAI AAA rules,
with optional training database weighting (least-trained formations first).
"""

import random
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

from training_db import ALL_RANDOMS, ALL_BLOCKS, TrainingDatabase

try:
    import formation_db
    FAI_RANDOM_NAMES = {f.code: f.name for f in formation_db.get_all_formations() if not f.is_block}
    FAI_BLOCK_NAMES = {f.code: f.name for f in formation_db.get_all_formations() if f.is_block}
except Exception:
    FAI_RANDOM_NAMES = {}
    FAI_BLOCK_NAMES = {}


@dataclass
class GeneratedRound:
    round_number: int
    formations: List[str]
    total_points: int
    draw_string: str
    formation_names: List[str]

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "formations": self.formations,
            "total_points": self.total_points,
            "draw_string": self.draw_string,
            "formation_names": self.formation_names,
        }


class DrawGenerator:
    """
    Generates multi-round draws for 4-Way Formation Skydiving.
    Adheres strictly to FAI AAA rules:
    - 5 to 6 points per round (never exceeding 6 points).
    - Blocks are worth 2 points, Randoms are worth 1 point.
    - No duplicate formation within the same round.
    - Non-repeating pools until pool depletion.
    """

    def __init__(self, training_db: Optional[TrainingDatabase] = None):
        self.training_db = training_db or TrainingDatabase()

    def generate_draw(
        self,
        num_rounds: int = 10,
        mode: str = "fai_aaa",
        seed: Optional[int] = None
    ) -> List[GeneratedRound]:
        """
        Generates a sequence of rounds.
        Modes:
            - 'fai_aaa': Official FAI Open (AAA) competition draw rules.
            - 'least_trained': Prioritizes least-trained formations from TrainingDatabase.
            - 'randoms_only': Rounds built only from Random formations (5-6 points).
            - 'blocks_only': Rounds built only from Blocks (3 blocks = 6 points).
        """
        if seed is not None:
            random.seed(seed)

        # Working pools
        available_blocks: List[str] = []
        available_randoms: List[str] = []

        rounds: List[GeneratedRound] = []

        for r_idx in range(1, num_rounds + 1):
            round_forms: List[str] = []
            round_points = 0

            # Continue drawing formations until reaching 5 or 6 points
            while round_points < 5:
                # Refill pools if exhausted
                if not available_blocks:
                    available_blocks = self._refill_pool(ALL_BLOCKS, mode, "blocks")
                if not available_randoms:
                    available_randoms = self._refill_pool(ALL_RANDOMS, mode, "randoms")

                remaining_needed = 6 - round_points

                # If we need 1 point (at 5 points), we CANNOT add a 2-point block!
                # We can either draw a Random (making it 6) or stop at 5 points.
                if remaining_needed == 1:
                    # Choose whether to finish at 5 points (50% chance) or add 1 random to reach 6 points
                    if mode == "blocks_only":
                        break
                    if random.choice([True, False]) and mode != "randoms_only":
                        break  # Stop at 5 points
                    # Pick a random
                    candidate = self._pick_from_pool(available_randoms, round_forms)
                    if candidate:
                        round_forms.append(candidate)
                        round_points += 1
                    break

                # If remaining_needed >= 2, we can choose between a Block (2 pts) or a Random (1 pt)
                if mode == "blocks_only":
                    choose_block = True
                elif mode == "randoms_only":
                    choose_block = False
                else:
                    # In standard FAI AAA, blocks make up roughly 50-60% of drawn points
                    choose_block = random.choice([True, True, False])

                if choose_block and available_blocks:
                    candidate = self._pick_from_pool(available_blocks, round_forms)
                    if candidate:
                        round_forms.append(candidate)
                        round_points += 2
                    else:
                        # Fallback to random if no unused block available for this round
                        candidate_rand = self._pick_from_pool(available_randoms, round_forms)
                        if candidate_rand:
                            round_forms.append(candidate_rand)
                            round_points += 1
                else:
                    candidate = self._pick_from_pool(available_randoms, round_forms)
                    if candidate:
                        round_forms.append(candidate)
                        round_points += 1

            # Format names
            names = []
            for f in round_forms:
                if f.isdigit():
                    names.append(FAI_BLOCK_NAMES.get(f, f"Block {f}"))
                else:
                    names.append(FAI_RANDOM_NAMES.get(f, f))

            draw_str = " - ".join(round_forms)
            rounds.append(GeneratedRound(
                round_number=r_idx,
                formations=round_forms,
                total_points=round_points,
                draw_string=draw_str,
                formation_names=names
            ))

        return rounds

    def _refill_pool(self, base_pool: List[str], mode: str, pool_type: str) -> List[str]:
        """Refills and orders the candidate pool according to selected mode."""
        if mode == "least_trained":
            # Sort by least trained count with slight randomness
            least_list = self.training_db.get_least_trained_formations(pool_type)
            codes = [c for c, _ in least_list if c in base_pool]
            # Add small random jitter so it doesn't always produce identical order
            def sort_key(code):
                stat = self.training_db.formation_stats.get(code)
                cnt = stat.jump_count if stat else 0
                return cnt + random.uniform(0.0, 0.4)
            return sorted(codes, key=sort_key)
        else:
            shuffled = list(base_pool)
            random.shuffle(shuffled)
            return shuffled

    def _pick_from_pool(self, pool: List[str], exclude: List[str]) -> Optional[str]:
        """Picks and removes the first item from pool not in exclude list."""
        for i, item in enumerate(pool):
            if item not in exclude:
                return pool.pop(i)
        return None
