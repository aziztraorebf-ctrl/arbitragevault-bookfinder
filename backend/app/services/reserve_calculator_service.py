"""
Reserve Calculator Service for Income Smoothing.

Calculates income smoothing reserves to maintain stable monthly income
despite seasonality in the textbook arbitrage business.

Key concepts:
- Peak months: August-October (back to school)
- Trough months: May-July (summer break)
- Reserve: Money set aside during peak to cover trough gaps
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ReserveRecommendation:
    """
    Recommendation for income smoothing reserve.

    Attributes:
        recommended_reserve: Total reserve amount needed
        monthly_contribution: Amount to set aside each peak month
        months_to_build: Number of months to fully build reserve
        coverage_months: Number of trough months the reserve covers
        target_monthly_income: Desired stable monthly income
        safety_margin_pct: Safety margin percentage applied
    """
    recommended_reserve: float
    monthly_contribution: float
    months_to_build: int
    coverage_months: int
    target_monthly_income: float
    safety_margin_pct: float


def calculate_smoothing_reserve(
    target_monthly_income: float,
    avg_peak_monthly: float,
    avg_trough_monthly: float,
    trough_months: int = 5,
    safety_margin: float = 0.15,
) -> ReserveRecommendation:
    """
    Calculate income smoothing reserve for textbook arbitrage.

    This function determines how much reserve is needed to maintain
    stable monthly income during low-earning trough months.

    Algorithm:
    1. Calculate monthly_gap = max(0, target - trough)
    2. base_reserve = gap * trough_months
    3. reserve_with_margin = base_reserve * (1 + safety_margin)
    4. monthly_contribution = (peak - target) * 0.25 (25% of surplus)
    5. months_to_build = ceiling(reserve / contribution)

    Args:
        target_monthly_income: Desired stable monthly income
        avg_peak_monthly: Average income during peak months (Aug-Oct)
        avg_trough_monthly: Average income during trough months (May-Jul)
        trough_months: Number of trough months to cover (default 5)
        safety_margin: Additional margin for safety (default 15%)

    Returns:
        ReserveRecommendation with all calculated values
    """
    # Step 1: Calculate monthly gap
    monthly_gap = max(0.0, target_monthly_income - avg_trough_monthly)

    # Step 2: Calculate base reserve
    base_reserve = monthly_gap * trough_months

    # Step 3: Apply safety margin
    reserve_with_margin = base_reserve * (1.0 + safety_margin)

    # Step 4: Calculate monthly contribution from peak surplus
    # 25% of surplus income goes to reserve
    peak_surplus = max(0.0, avg_peak_monthly - target_monthly_income)
    monthly_contribution = peak_surplus * 0.25

    # Step 5: Calculate months to build reserve
    if reserve_with_margin <= 0:
        # No reserve needed
        months_to_build = 0
    elif monthly_contribution <= 0:
        # Cannot build from surplus alone
        months_to_build = -1
    else:
        # Round up to nearest month
        months_to_build = math.ceil(reserve_with_margin / monthly_contribution)

    return ReserveRecommendation(
        recommended_reserve=reserve_with_margin,
        monthly_contribution=monthly_contribution,
        months_to_build=months_to_build,
        coverage_months=trough_months,
        target_monthly_income=target_monthly_income,
        safety_margin_pct=safety_margin,
    )


def project_annual_income(
    monthly_projections: Dict[int, float],
    reserve_percentage: int = 25,
) -> Dict:
    """
    Project annual income with seasonality analysis.

    Analyzes monthly projections to identify peak/trough patterns
    and calculate reserve contributions.

    Args:
        monthly_projections: Dict mapping month (1-12) to projected profit
        reserve_percentage: Percentage of peak profits to reserve (default 25%)

    Returns:
        Dict containing:
        - annual_gross: Total annual gross income
        - annual_net: Net income after reserve contribution
        - peak_months: List of peak month numbers (top 4)
        - trough_months: List of trough month numbers (bottom 5)
        - avg_peak: Average income during peak months
        - avg_trough: Average income during trough months
        - reserve_contribution: Total reserve contribution from peaks
        - smoothed_monthly: Target smoothed monthly income
    """
    if not monthly_projections:
        return {
            'annual_gross': 0.0,
            'annual_net': 0.0,
            'peak_months': [],
            'trough_months': [],
            'avg_peak': 0.0,
            'avg_trough': 0.0,
            'reserve_contribution': 0.0,
            'smoothed_monthly': 0.0,
        }

    # Calculate annual gross
    annual_gross = sum(monthly_projections.values())

    # Sort months by income
    sorted_months = sorted(
        monthly_projections.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Identify peak months (top 4) and trough months (bottom 5)
    num_months = len(sorted_months)

    if num_months >= 4:
        peak_entries = sorted_months[:4]
        peak_months = [m[0] for m in peak_entries]
        peak_total = sum(m[1] for m in peak_entries)
        avg_peak = peak_total / 4
    else:
        peak_entries = sorted_months
        peak_months = [m[0] for m in peak_entries]
        peak_total = sum(m[1] for m in peak_entries)
        avg_peak = peak_total / len(peak_entries) if peak_entries else 0.0

    if num_months >= 5:
        trough_entries = sorted_months[-5:]
        trough_months = [m[0] for m in trough_entries]
        trough_total = sum(m[1] for m in trough_entries)
        avg_trough = trough_total / 5
    else:
        trough_entries = sorted_months
        trough_months = [m[0] for m in trough_entries]
        trough_total = sum(m[1] for m in trough_entries)
        avg_trough = trough_total / len(trough_entries) if trough_entries else 0.0

    # Calculate reserve contribution from peak profits
    reserve_contribution = peak_total * (reserve_percentage / 100.0)

    # Calculate annual net after reserve
    annual_net = annual_gross - reserve_contribution

    # Calculate smoothed monthly income
    smoothed_monthly = annual_net / 12 if annual_net > 0 else 0.0

    return {
        'annual_gross': annual_gross,
        'annual_net': annual_net,
        'peak_months': peak_months,
        'trough_months': trough_months,
        'avg_peak': avg_peak,
        'avg_trough': avg_trough,
        'reserve_contribution': reserve_contribution,
        'smoothed_monthly': smoothed_monthly,
    }


def get_capital_growth_projection(
    initial_capital: float,
    monthly_roi_pct: float = 50,
    reinvestment_rate: float = 75,
    months: int = 12,
) -> List[Dict]:
    """
    Project month-by-month capital growth with compound returns.

    Simulates business growth over time with reinvestment strategy.

    For each month:
    - gross_profit = starting_capital * (roi_pct / 100)
    - net_profit = gross_profit * 0.90 (10% for fees/costs)
    - reinvested = net_profit * (reinvestment_rate / 100)
    - pocket = net_profit - reinvested
    - ending_capital = starting_capital + reinvested

    Args:
        initial_capital: Starting capital amount
        monthly_roi_pct: Expected monthly ROI percentage (default 50%)
        reinvestment_rate: Percentage of net profit to reinvest (default 75%)
        months: Number of months to project (default 12)

    Returns:
        List of monthly projections, each containing:
        - month: Month number (1-based)
        - starting_capital: Capital at start of month
        - gross_profit: Gross profit for the month
        - net_profit: Net profit after fees (90% of gross)
        - reinvested: Amount reinvested
        - pocket: Amount taken as income
        - ending_capital: Capital at end of month
    """
    if months <= 0:
        return []

    projections = []
    current_capital = initial_capital

    for month_num in range(1, months + 1):
        # Calculate gross profit
        gross_profit = current_capital * (monthly_roi_pct / 100.0)

        # Calculate net profit (90% of gross - 10% for fees/costs)
        net_profit = gross_profit * 0.90

        # Calculate reinvestment and pocket money
        reinvested = net_profit * (reinvestment_rate / 100.0)
        pocket = net_profit - reinvested

        # Calculate ending capital
        ending_capital = current_capital + reinvested

        projections.append({
            'month': month_num,
            'starting_capital': current_capital,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'reinvested': reinvested,
            'pocket': pocket,
            'ending_capital': ending_capital,
        })

        # Update capital for next month
        current_capital = ending_capital

    return projections
