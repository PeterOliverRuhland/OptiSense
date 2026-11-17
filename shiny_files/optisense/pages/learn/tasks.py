"""The fixed practice tasks: 15 named tasks, 5 per variable type – integer, continuous, mixed (Robin, 2026-11-17).

Every task has its topic for good (Workshop, Rice mill, Bakery …), which tells the story around the numbers, and the
topic fits the variable type: what you count is integer, what you measure (tons, hectares, kg, liters in bulk)
continuous, a mixed topic has one of each (engine.TOPICS). Every task comes on both levels – 2 constraints, or 3
with some cost problems (only with topics that make sense as costs). Burger and Shawarma have a story of their own:
on level 2 with the 3 constraints of the lecture, on level 1 with bread and meat only. The start page lists the 15
names; the learner picks one or leaves it to chance. Made by tools/make_task_pool.py (see there for what makes a task good) and checked in
tests/test_learning.py: every value the learner works out is whole or ends in ,5. A row is (a1, a2, op, b):
a1·x1 + a2·x2 op b; the rows are the two resources and, on level 2, the total x1 + x2 ≤ b. Ids stay fixed: they name
a task in the logs.
"""

POOL = {
    ("easy", "LP"): [
        {"id": "LP-1-01", "topic": "farming", "sense": "max", "kind": "LP", "c": (6, 4), "rows": [(1, 4, "<=", 32), (6, 3, "<=", 45)]},
        {"id": "LP-1-04", "topic": "feed", "sense": "max", "kind": "LP", "c": (4, 7), "rows": [(3, 6, "<=", 60), (3, 1, "<=", 22.5)]},
        {"id": "LP-1-07", "topic": "rice", "sense": "max", "kind": "LP", "c": (9, 7), "rows": [(2, 4, "<=", 46), (5, 2, "<=", 55)]},
        {"id": "LP-1-10", "topic": "soil", "sense": "max", "kind": "LP", "c": (6, 3), "rows": [(3, 6, "<=", 36), (6, 1, "<=", 39)]},
        {"id": "LP-1-13", "topic": "coffee", "sense": "max", "kind": "LP", "c": (9, 5), "rows": [(3, 3, "<=", 40.5), (6, 3, "<=", 63)]},
    ],
    ("easy", "ILP"): [
        {"id": "ILP-1-01", "topic": "production", "sense": "max", "kind": "ILP", "c": (7, 8), "rows": [(2, 6, "<=", 39), (4, 1, "<=", 34)]},
        {"id": "ILP-1-06", "topic": "print", "sense": "max", "kind": "ILP", "c": (4, 6), "rows": [(3, 4, "<=", 30), (3, 2, "<=", 21)]},
        {"id": "ILP-1-11", "topic": "transport", "sense": "max", "kind": "ILP", "c": (5, 4), "rows": [(3, 3, "<=", 49.5), (6, 3, "<=", 75)]},
        # Burger and Shawarma with bread and meat only – you cannot eat them without bread (Robin, 2026-11-17)
        {"id": "ILP-1-BURGER", "story": "burger", "sense": "max", "kind": "ILP", "c": (4.5, 6), "rows": [(1, 1, "<=", 500), (0.1, 0.3, "<=", 105)]},
        {"id": "ILP-1-SHAWARMA", "story": "shawarma", "sense": "max", "kind": "ILP", "c": (80, 100), "rows": [(1, 1, "<=", 300), (0.1, 0.2, "<=", 40)]},
    ],
    ("easy", "MILP"): [
        {"id": "MILP-1-01", "topic": "bakery", "sense": "max", "kind": "MILP1", "c": (10, 4), "rows": [(3, 3, "<=", 34.5), (6, 3, "<=", 57)]},
        {"id": "MILP-1-04", "topic": "farmshop", "sense": "max", "kind": "MILP1", "c": (5, 3), "rows": [(3, 3, "<=", 28.5), (5, 1, "<=", 27.5)]},
        {"id": "MILP-1-07", "topic": "fish", "sense": "max", "kind": "MILP1", "c": (7, 5), "rows": [(2, 3, "<=", 24), (6, 3, "<=", 54)]},
        {"id": "MILP-1-09", "topic": "canteen", "sense": "max", "kind": "MILP2", "c": (6, 7), "rows": [(3, 3, "<=", 25.5), (6, 1, "<=", 36)]},
        {"id": "MILP-1-12", "topic": "dairy", "sense": "max", "kind": "MILP2", "c": (7, 9), "rows": [(3, 3, "<=", 40.5), (6, 2, "<=", 51)]},
    ],
    ("medium", "LP"): [
        {"id": "LP-2-01", "topic": "farming", "sense": "max", "kind": "LP", "c": (4, 6), "rows": [(3, 6, "<=", 69), (6, 2, "<=", 63), (1, 1, "<=", 15)]},
        {"id": "LP-2-04", "topic": "rice", "sense": "max", "kind": "LP", "c": (7, 11), "rows": [(3, 6, "<=", 57), (5, 2, "<=", 35), (1, 1, "<=", 10)]},
        {"id": "LP-2-07", "topic": "coffee", "sense": "max", "kind": "LP", "c": (5, 4), "rows": [(3, 6, "<=", 60), (3, 1, "<=", 30), (1, 1, "<=", 13)]},
        {"id": "LP-2-10", "topic": "feed", "sense": "min", "kind": "LP", "c": (5, 6), "rows": [(1, 5, ">=", 30), (6, 3, ">=", 45), (1, 1, "<=", 15)]},
        {"id": "LP-2-13", "topic": "soil", "sense": "min", "kind": "LP", "c": (8, 4), "rows": [(1, 3, ">=", 25.5), (5, 2, ">=", 30), (1, 1, "<=", 17)]},
    ],
    ("medium", "ILP"): [
        {"id": "ILP-2-01", "topic": "production", "sense": "max", "kind": "ILP", "c": (7, 5), "rows": [(3, 6, "<=", 33), (4, 1, "<=", 16), (1, 1, "<=", 6)]},
        {"id": "ILP-2-05", "topic": "print", "sense": "max", "kind": "ILP", "c": (9, 12), "rows": [(1, 3, "<=", 31.5), (3, 1, "<=", 34.5), (1, 1, "<=", 16)]},
        {"id": "ILP-2-10", "topic": "transport", "sense": "min", "kind": "ILP", "c": (10, 9), "rows": [(1, 3, ">=", 25.5), (4, 1, ">=", 36), (1, 1, "<=", 16)]},
        # two tasks with a story of their own (texts learn_<story>_*), never told with another topic: the burger problem
        # of the lecture (Prof. Koot, Aalen University; also the example of “Model & solution”) and the shawarma stand
        # of the guided task, here graded. Their rows follow the story, the bread first. Their optimal corners are
        # already whole, so – unlike the other integer tasks – they keep the corner step (also on level 1).
        {"id": "ILP-2-BURGER", "story": "burger", "sense": "max", "kind": "ILP", "c": (4.5, 6),
         "rows": [(1, 1, "<=", 500), (0.1, 0.3, "<=", 105), (0.1, 0.15, "<=", 60)]},
        {"id": "ILP-2-SHAWARMA", "story": "shawarma", "sense": "max", "kind": "ILP", "c": (80, 100),
         "rows": [(1, 1, "<=", 300), (0.1, 0.2, "<=", 40), (0.1, 0.05, "<=", 27)]},
    ],
    ("medium", "MILP"): [
        {"id": "MILP-2-01", "topic": "bakery", "sense": "max", "kind": "MILP1", "c": (10, 3), "rows": [(3, 5, "<=", 52.5), (3, 1, "<=", 22.5), (1, 1, "<=", 12)]},
        {"id": "MILP-2-04", "topic": "farmshop", "sense": "max", "kind": "MILP2", "c": (10, 11), "rows": [(3, 5, "<=", 60), (6, 3, "<=", 57), (1, 1, "<=", 13)]},
        {"id": "MILP-2-07", "topic": "dairy", "sense": "max", "kind": "MILP2", "c": (5, 3), "rows": [(2, 4, "<=", 42), (3, 1, "<=", 25.5), (1, 1, "<=", 11)]},
        {"id": "MILP-2-10", "topic": "canteen", "sense": "min", "kind": "MILP1", "c": (8, 12), "rows": [(3, 3, ">=", 43.5), (4, 1, ">=", 40), (1, 1, "<=", 22)]},
        {"id": "MILP-2-15", "topic": "fish", "sense": "min", "kind": "MILP2", "c": (12, 7), "rows": [(3, 5, ">=", 67.5), (3, 3, ">=", 49.5), (1, 1, "<=", 22)]},
    ],
}

