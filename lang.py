import yfinance as yf
import numpy as np
import heapq
import matplotlib.pyplot as plt
import pandas as pd


# Step 1: Fetch Real-Time Financial Data (Stocks, Bonds, etc.)
def get_asset_data(asset_symbol):
    """
    Fetch historical stock data for the given symbol and calculate expected return and risk.
    """
    try:
        data = yf.download(asset_symbol, period='5y')  # 5-year historical data

        if data.empty:
            raise ValueError(f"No data found for {asset_symbol}")

        returns = data['Adj Close'].pct_change().dropna()

        expected_return = np.mean(returns) * 252  # Annualized return
        risk = np.std(returns, axis=0) * np.sqrt(252)  # Annualized volatility with correct axis

        # Convert to scalar if it's an array or series
        if isinstance(expected_return, (np.ndarray, pd.Series)):
            expected_return = expected_return.item()
        if isinstance(risk, (np.ndarray, pd.Series)):
            risk = risk.item()

        return expected_return, risk
    except Exception as e:
        raise ValueError(f"Error fetching data for {asset_symbol}: {str(e)}")


# Step 2: Calculate Sharpe Ratio (Risk-Return Trade-Off)
def sharpe_ratio(expected_return, risk, risk_free_rate=0.01):
    """
    Calculate the Sharpe Ratio to assess risk-adjusted return.
    """
    return (expected_return - risk_free_rate) / risk


# Step 3: Define Portfolio Optimization Class (A* Algorithm) with Improvements
class PortfolioOptimizationAStar:
    def __init__(self, assets, expected_returns, risks, budget, risk_tolerance):
        """
        :param assets: List of available assets (stock symbols).
        :param expected_returns: List of expected returns for each asset.
        :param risks: List of risks (volatility) for each asset.
        :param budget: Total investment budget.
        :param risk_tolerance: Client's risk tolerance (conservative, balanced, aggressive).
        """
        self.assets = assets
        self.expected_returns = expected_returns
        self.risks = risks
        self.budget = budget
        self.risk_tolerance = risk_tolerance
        self.increment = 0.1  # Increased step increment for faster convergence (10%)

    def heuristic(self, allocation):
        """
        Heuristic to estimate risk-adjusted future return based on Sharpe Ratio and risk tolerance.
        """
        total_return = sum(self.expected_returns[i] * allocation[i] for i in range(len(self.assets)))
        total_risk = sum(self.risks[i] * allocation[i] for i in range(len(self.assets)))

        # Risk-adjusted return, adjusted for client's risk tolerance
        risk_adjusted_return = total_return - self.risk_tolerance * total_risk

        return -risk_adjusted_return  # A* minimizes cost, so we negate to maximize return

    def is_valid_allocation(self, allocation):
        """
        Check if the allocation is valid (does not exceed the budget and ensures diversification).
        """
        total_allocation = sum(allocation)
        max_percentage_per_asset = 0.7  # Allow up to 70% allocation to a single asset
        return abs(total_allocation - self.budget) < 0.01 and \
            all(0 <= a <= max_percentage_per_asset * self.budget for a in allocation)

    def generate_neighbors(self, allocation):
        """
        Generate neighboring allocations by incrementing the allocation of each asset by a fixed step.
        """
        neighbors = []
        for i in range(len(self.assets)):
            new_allocation = allocation[:]
            if new_allocation[i] + self.increment <= self.budget:  # Increment within the budget
                new_allocation[i] += self.increment
                if sum(new_allocation) <= self.budget:  # Ensure we don't exceed the budget
                    neighbors.append(new_allocation)
        return neighbors

    def astar_optimization(self):
        """
        A* algorithm to find the optimal portfolio allocation.
        """
        n = len(self.assets)
        pq = []  # Priority queue to explore states
        start_state = [0] * n  # Start with no allocation
        start_cost = self.heuristic(start_state)

        heapq.heappush(pq, (start_cost, start_state))
        visited = set()

        while pq:
            current_cost, current_allocation = heapq.heappop(pq)

            # Early stop if allocation reaches the exact budget
            if abs(sum(current_allocation) - self.budget) < 0.01 and self.is_valid_allocation(current_allocation):
                return [a * 100 / self.budget for a in current_allocation]  # Convert to percentage

            # Debugging print: allocation being tested
            print(f"Testing allocation: {current_allocation}, cost: {current_cost:.2f}")

            # Generate and test neighbors
            for neighbor in self.generate_neighbors(current_allocation):
                if tuple(neighbor) not in visited:
                    new_cost = self.heuristic(neighbor)
                    heapq.heappush(pq, (new_cost, neighbor))
                    visited.add(tuple(neighbor))

        return None  # No valid allocation found


# Step 4: Gather Client Information (Ask for User Input)
def gather_client_info():
    """
    Gather client information (investment amount, risk tolerance) from user input.
    """
    try:
        budget = float(input("Enter your total investment amount: "))
    except ValueError:
        print("Invalid input! Please enter a valid number.")
        return gather_client_info()

    risk_tolerance_map = {'1': 0.5, '2': 1.0, '3': 1.5}
    risk_tolerance = input("Enter your risk tolerance (1: Conservative, 2: Balanced, 3: Aggressive): ")

    if risk_tolerance not in risk_tolerance_map:
        print("Invalid risk tolerance! Please enter a number between 1 and 3.")
        return gather_client_info()

    return budget, risk_tolerance_map[risk_tolerance]


# Step 5: Plot the Portfolio Allocation (For Client Presentation)
def plot_portfolio(assets, allocation):
    """
    Plot the asset allocation in a pie chart for client presentation.
    """
    plt.pie(allocation, labels=assets, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures pie chart is drawn as a circle.
    plt.title('Optimal Portfolio Allocation')
    plt.show()


# Main function to optimize portfolio based on real-time data and client preferences
def main():
    # Get asset list from the user
    print("Enter the asset symbols (stock tickers) you want to include in the portfolio (comma-separated):")
    asset_input = input()
    assets = [asset.strip().upper() for asset in asset_input.split(",")]

    # Fetch expected returns and risks for each asset
    expected_returns = []
    risks = []
    for asset in assets:
        try:
            exp_return, risk = get_asset_data(asset)

            # Ensure the values are scalar (convert from Series or array if necessary)
            if isinstance(exp_return, (np.ndarray, pd.Series)):
                exp_return = exp_return.item()
            if isinstance(risk, (np.ndarray, pd.Series)):
                risk = risk.item()

            expected_returns.append(exp_return)
            risks.append(risk)
            print(f"{asset}: Expected Return: {exp_return:.2%}, Risk: {risk:.2%}")
        except Exception as e:
            print(f"Error fetching data for {asset}: {e}")

    # Gather client information
    budget, risk_tolerance = gather_client_info()

    # Initialize and run the A* Portfolio Optimization
    portfolio_optimizer = PortfolioOptimizationAStar(assets, expected_returns, risks, budget, risk_tolerance)
    optimal_allocation = portfolio_optimizer.astar_optimization()

    if optimal_allocation:
        print("Optimal Portfolio Allocation:")
        for i, allocation in enumerate(optimal_allocation):
            print(f"{assets[i]}: {allocation:.2f}%")

        # Plot the allocation for visualization
        plot_portfolio(assets, optimal_allocation)
    else:
        print("No valid portfolio allocation found.")


if __name__ == "__main__":
    main()