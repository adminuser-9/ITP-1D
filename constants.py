"""Fixed booking rules. All prices are integer cents (100 cents = SGD $1)."""

ADULT_PRICE = 1000
CHILD_PRICE = 500
SENIOR_PRICE = 700
GUIDE_PRICE = 300
BOOKLET_PRICE = 400
FAMILY_PRICE = 2500
OFF_PEAK_PERCENT = 80
GROUP_PERCENT = 90
GROUP_MINIMUM = 10
MAX_VISITORS = 20
MAX_BOOKLETS = 20
PERIODS = ("Peak", "Off-Peak")
QUANTITY_FIELDS = ("adults", "children", "seniors", "infants", "guides", "booklets")
VISITOR_CATEGORIES = (
    ("adults", "Number of adults (ages 13–59)", ADULT_PRICE),
    ("children", "Number of children (ages 4–12)", CHILD_PRICE),
    ("seniors", "Number of seniors (ages 60 and above)", SENIOR_PRICE),
    ("infants", "Number of infants (ages 0–3)", 0),
)
