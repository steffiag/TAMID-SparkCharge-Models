""" Future Growth Model

Projects revenue, cost, and profit year by year for each partner under
Low / Medium / High growth scenarios, then rolls them up into a portfolio
total with cumulative profit and NPV.

Year 1 for each partner matches the inputs in the current revenue build.
Every growth rate and capacity number below is a PLACEHOLDER assumption.
Swap in sourced numbers before presenting.

Activating Virtual Environment: # source .venv/bin/activate

Values we need for each partner (on top of the revenue build inputs):
    - Year the partner goes live
    - Year 1 EVs served for each scenario
    - Annual cost of one deployed charging unit
    - How many sessions one unit can handle per year

Values we need for each growth scenario:
    - Yearly growth in EVs served
    - Yearly growth in sessions per EV
    - Yearly change in revenue per session
    - Yearly cost inflation
"""

import csv
from dataclasses import dataclass
from math import ceil

import matplotlib.pyplot as plt

START_YEAR = 2027
YEARS = 5
DISCOUNT_RATE = 0.10  # used for NPV of profit
CSV_PATH = "growth_projection.csv"


@dataclass
class GrowthScenario:
    name: str
    ev_growth: float               # yearly growth in EVs served
    sessions_per_ev_growth: float  # yearly growth in sessions per EV
    price_growth: float            # yearly change in revenue per session
    cost_inflation: float          # yearly change in per-session and per-unit costs


@dataclass
class Partner:
    name: str
    partner_type: str
    start_year: int
    year1_evs: dict[str, int]      # starting EVs served, keyed by scenario name
    sessions_per_ev_per_year: float
    revenue_per_session: float     # in START_YEAR dollars
    cost_per_session: float        # in START_YEAR dollars
    annual_cost_per_unit: float    # fixed cost of one charging unit per year, START_YEAR dollars
    unit_capacity_sessions: int    # max sessions one unit can handle per year


@dataclass
class YearResult:
    scenario: str
    partner: str
    year: int
    evs: float
    sessions: float
    units: int
    revenue: float
    cost: float
    profit: float


SCENARIOS = [
    GrowthScenario("Low", ev_growth=0.05, sessions_per_ev_growth=0.00, price_growth=0.00, cost_inflation=0.04),
    GrowthScenario("Medium", ev_growth=0.15, sessions_per_ev_growth=0.03, price_growth=0.02, cost_inflation=0.03),
    GrowthScenario("High", ev_growth=0.30, sessions_per_ev_growth=0.05, price_growth=0.03, cost_inflation=0.025),
]

PARTNERS = [
    Partner(
        name="Northeastern University",
        partner_type="University",
        start_year=2027,
        year1_evs={"Low": 40, "Medium": 100, "High": 160},
        sessions_per_ev_per_year=18,
        revenue_per_session=25,
        cost_per_session=13,
        annual_cost_per_unit=18_000,
        unit_capacity_sessions=3_000,  # about 8 sessions a day, placeholder
    ),
    Partner(
        name="Avalon North Station",
        partner_type="Residential property",
        start_year=2027,
        year1_evs={"Low": 25, "Medium": 50, "High": 100},
        sessions_per_ev_per_year=12,
        revenue_per_session=25,
        cost_per_session=15,
        annual_cost_per_unit=12_000,
        unit_capacity_sessions=3_000,
    ),
    # Template for a partner that signs on in a later year. Uncomment and edit.
    # Partner(
    #     name="New partner",
    #     partner_type="Fleet depot",
    #     start_year=2029,
    #     year1_evs={"Low": 30, "Medium": 60, "High": 120},
    #     sessions_per_ev_per_year=50,
    #     revenue_per_session=25,
    #     cost_per_session=14,
    #     annual_cost_per_unit=15_000,
    #     unit_capacity_sessions=3_000,
    # ),
]


def project(partner: Partner, scenario: GrowthScenario) -> list[YearResult]:
    results = []

    for year in range(START_YEAR, START_YEAR + YEARS):
        if year < partner.start_year:
            continue

        years_live = year - partner.start_year     # drives adoption growth at this site
        years_elapsed = year - START_YEAR          # drives price and cost changes

        evs = partner.year1_evs[scenario.name] * (1 + scenario.ev_growth) ** years_live
        sessions_per_ev = partner.sessions_per_ev_per_year * (1 + scenario.sessions_per_ev_growth) ** years_live
        sessions = evs * sessions_per_ev

        price = partner.revenue_per_session * (1 + scenario.price_growth) ** years_elapsed
        inflation = (1 + scenario.cost_inflation) ** years_elapsed

        # Fixed cost steps up when demand outgrows the units on site
        units = max(1, ceil(sessions / partner.unit_capacity_sessions))

        revenue = sessions * price
        cost = (units * partner.annual_cost_per_unit + sessions * partner.cost_per_session) * inflation

        results.append(
            YearResult(scenario.name, partner.name, year, evs, sessions, units, revenue, cost, revenue - cost)
        )

    return results


def npv(cash_flows: list[float], rate: float) -> float:
    # End-of-year convention, so year 1 is discounted one period
    return sum(cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cash_flows))


years = list(range(START_YEAR, START_YEAR + YEARS))
all_results: list[YearResult] = []
portfolio_profit: dict[str, list[float]] = {}

for scenario in SCENARIOS:
    print(f"\n{'=' * 78}\n{scenario.name.upper()} GROWTH SCENARIO\n{'=' * 78}")

    totals = {year: {"revenue": 0.0, "cost": 0.0, "profit": 0.0} for year in years}

    for partner in PARTNERS:
        results = project(partner, scenario)
        all_results.extend(results)

        first_profitable = next((r.year for r in results if r.profit > 0), None)
        print(f"\n{partner.name} | {partner.partner_type} | "
              f"first profitable year: {first_profitable or 'not within projection'}")

        for r in results:
            totals[r.year]["revenue"] += r.revenue
            totals[r.year]["cost"] += r.cost
            totals[r.year]["profit"] += r.profit
            print(
                f"  {r.year} | {r.evs:6.0f} EVs | {r.sessions:7,.0f} sessions | {r.units} unit(s) | "
                f"Revenue ${r.revenue:>10,.0f} | Cost ${r.cost:>10,.0f} | Profit ${r.profit:>10,.0f}"
            )

    yearly_profit = [totals[year]["profit"] for year in years]
    portfolio_profit[scenario.name] = yearly_profit

    print("\nPortfolio total")
    cumulative = 0.0
    for year in years:
        cumulative += totals[year]["profit"]
        print(
            f"  {year} | Revenue ${totals[year]['revenue']:>10,.0f} | Cost ${totals[year]['cost']:>10,.0f} | "
            f"Profit ${totals[year]['profit']:>10,.0f} | Cumulative ${cumulative:>10,.0f}"
        )
    print(f"  {YEARS}-year NPV of profit at {DISCOUNT_RATE:.0%}: ${npv(yearly_profit, DISCOUNT_RATE):,.0f}")

with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["scenario", "partner", "year", "evs", "sessions", "units", "revenue", "cost", "profit"])
    for r in all_results:
        writer.writerow([r.scenario, r.partner, r.year, round(r.evs, 1), round(r.sessions, 1),
                         r.units, round(r.revenue, 2), round(r.cost, 2), round(r.profit, 2)])
print(f"\nSaved full projection to {CSV_PATH}")

fig, (annual_ax, cumulative_ax, partner_ax) = plt.subplots(1, 3, figsize=(17, 5))

for scenario in SCENARIOS:
    profits = portfolio_profit[scenario.name]
    running, cumulative_profits = 0.0, []
    for p in profits:
        running += p
        cumulative_profits.append(running)

    annual_ax.plot(years, profits, marker="o", label=scenario.name)
    cumulative_ax.plot(years, cumulative_profits, marker="o", label=scenario.name)

# Medium scenario broken out by partner
bar_width = 0.8 / len(PARTNERS)
for i, partner in enumerate(PARTNERS):
    partner_profits = {r.year: r.profit for r in all_results if r.scenario == "Medium" and r.partner == partner.name}
    heights = [partner_profits.get(year, 0) for year in years]
    offsets = [year - 0.4 + bar_width * (i + 0.5) for year in years]
    partner_ax.bar(offsets, heights, width=bar_width, label=partner.name)

annual_ax.set(title="Annual portfolio profit", xlabel="Year", ylabel="Profit ($)")
cumulative_ax.set(title="Cumulative portfolio profit", xlabel="Year", ylabel="Cumulative profit ($)")
partner_ax.set(title="Profit by partner (Medium scenario)", xlabel="Year", ylabel="Profit ($)")

for ax in (annual_ax, cumulative_ax, partner_ax):
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.set_xticks(years)
    ax.legend(fontsize=8)

fig.tight_layout()
plt.savefig("growth_charts.png", dpi=150)
