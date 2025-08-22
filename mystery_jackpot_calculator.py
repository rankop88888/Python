# ═══════════════════════════════════════════════════════════════════════════════════
#  Enhanced Mystery Jackpot Contribution Calculator  •  v3.0
#  Advanced gaming industry tool for jackpot contribution analysis
# ═══════════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

# ═══════════════════════════════════════════════════════════════════════════════════
# Configuration & Setup
# ═══════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Mystery Jackpot Calculator",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f4e79;
    text-align: center;
    margin-bottom: 2rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin: 0.5rem;
}
.warning-box {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 0.75rem;
    border-radius: 5px;
    margin: 0.5rem 0;
}
.success-box {
    background-color: #d1edff;
    border: 1px solid #74b9ff;
    color: #0984e3;
    padding: 0.75rem;
    border-radius: 5px;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════
# Data Classes & Models
# ═══════════════════════════════════════════════════════════════════════════════════

@dataclass
class JackpotLevel:
    """Represents a single jackpot level with all its parameters."""
    level: int
    coin_in: float
    initial_jp: float
    min_hit: float
    max_hit: float
    contribution_pct: float
    
    @property
    def avg_hit(self) -> float:
        """Average hit amount between min and max."""
        return (self.min_hit + self.max_hit) / 2.0
    
    @property
    def build_amount(self) -> float:
        """Amount needed to build from initial to average hit."""
        return max(self.avg_hit - self.initial_jp, 0)
    
    @property
    def daily_contribution(self) -> float:
        """Daily contribution amount."""
        return self.coin_in * (self.contribution_pct / 100)
    
    @property
    def hit_frequency_days(self) -> float:
        """Expected days to hit based on contribution rate."""
        if self.daily_contribution <= 0:
            return float('inf')
        return self.build_amount / self.daily_contribution
    
    @property
    def effective_percentage(self) -> float:
        """Effective percentage considering initial seed."""
        if self.build_amount <= 0:
            return 0.0
        return self.contribution_pct * (self.avg_hit / self.build_amount)
    
    @property
    def is_valid(self) -> Tuple[bool, List[str]]:
        """Check if level data is valid and return errors."""
        errors = []
        
        if self.coin_in <= 0:
            errors.append("Coin-In must be greater than 0")
        if self.initial_jp < 0:
            errors.append("Initial Jackpot cannot be negative")
        if self.min_hit < 0:
            errors.append("Min Hit cannot be negative")
        if self.max_hit < self.min_hit:
            errors.append("Max Hit must be greater than or equal to Min Hit")
        if not (0 <= self.contribution_pct <= 100):
            errors.append("Contribution percentage must be between 0-100%")
        if self.min_hit < self.initial_jp:
            errors.append("Min Hit should be greater than or equal to Initial Jackpot")
            
        return len(errors) == 0, errors

# ═══════════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════════

class NumberFormatter:
    """Handle number parsing and formatting with international support."""
    
    DOT_GROUPS = re.compile(r"[.\s,]")
    
    @staticmethod
    def parse_number(text: str) -> float:
        """Parse text input to number, handling various formats."""
        if not text or text.strip() == "":
            return 0.0
        
        # Remove common separators
        clean_text = NumberFormatter.DOT_GROUPS.sub("", text.strip())
        
        try:
            return float(clean_text) if clean_text else 0.0
        except ValueError:
            return 0.0
    
    @staticmethod
    def format_currency(amount: float, currency: str = "") -> str:
        """Format number as currency with thousand separators."""
        formatted = f"{int(round(amount)):,}".replace(",", ".")
        return f"{formatted} {currency}".strip()
    
    @staticmethod
    def format_percentage(pct: float, decimals: int = 2) -> str:
        """Format percentage with specified decimal places."""
        return f"{pct:.{decimals}f}%"

class ChartGenerator:
    """Generate enhanced charts with consistent styling."""
    
    @staticmethod
    def setup_style():
        """Setup matplotlib and seaborn styling."""
        plt.style.use('default')
        sns.set_palette("husl")
        
    @staticmethod
    def create_bar_chart(x_data: List, y_data: List, title: str, 
                        xlabel: str, ylabel: str, color_palette: str = "viridis") -> plt.Figure:
        """Create enhanced bar chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(x_data, y_data, color=plt.cm.get_cmap(color_palette)(range(len(x_data))))
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height != float('inf'):
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_comparison_chart(levels: List[JackpotLevel]) -> plt.Figure:
        """Create multi-metric comparison chart."""
        if not levels:
            return plt.figure()
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        level_nums = [lvl.level for lvl in levels]
        
        # Raw vs Effective Percentage
        raw_pcts = [lvl.contribution_pct for lvl in levels]
        eff_pcts = [lvl.effective_percentage for lvl in levels]
        
        x = range(len(level_nums))
        width = 0.35
        
        ax1.bar([i - width/2 for i in x], raw_pcts, width, label='Raw %', alpha=0.8)
        ax1.bar([i + width/2 for i in x], eff_pcts, width, label='Effective %', alpha=0.8)
        ax1.set_title('Raw vs Effective Contribution %')
        ax1.set_xlabel('Level')
        ax1.set_ylabel('Percentage')
        ax1.set_xticks(x)
        ax1.set_xticklabels(level_nums)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Hit Frequency
        hit_days = [lvl.hit_frequency_days if lvl.hit_frequency_days != float('inf') else 0 for lvl in levels]
        ax2.bar(level_nums, hit_days, color='coral', alpha=0.8)
        ax2.set_title('Hit Frequency (Days)')
        ax2.set_xlabel('Level')
        ax2.set_ylabel('Days')
        ax2.grid(True, alpha=0.3)
        
        # Daily Contribution
        daily_contribs = [lvl.daily_contribution for lvl in levels]
        ax3.bar(level_nums, daily_contribs, color='lightgreen', alpha=0.8)
        ax3.set_title('Daily Contribution Amount')
        ax3.set_xlabel('Level')
        ax3.set_ylabel('Amount')
        ax3.grid(True, alpha=0.3)
        
        # Average Hit vs Initial
        initial_amounts = [lvl.initial_jp for lvl in levels]
        avg_hits = [lvl.avg_hit for lvl in levels]
        
        ax4.bar([i - width/2 for i in x], initial_amounts, width, label='Initial JP', alpha=0.8)
        ax4.bar([i + width/2 for i in x], avg_hits, width, label='Avg Hit', alpha=0.8)
        ax4.set_title('Initial JP vs Average Hit')
        ax4.set_xlabel('Level')
        ax4.set_ylabel('Amount')
        ax4.set_xticks(x)
        ax4.set_xticklabels(level_nums)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

# ═══════════════════════════════════════════════════════════════════════════════════
# Session State Management
# ═══════════════════════════════════════════════════════════════════════════════════

def initialize_session_state():
    """Initialize session state with default values."""
    if "levels_data" not in st.session_state:
        st.session_state.levels_data = [
            {"coin": "", "init": "", "min": "", "max": "", "pct": "0.00"}
        ]
    if "currency" not in st.session_state:
        st.session_state.currency = "$"
    if "show_advanced" not in st.session_state:
        st.session_state.show_advanced = False

def save_configuration():
    """Save current configuration to downloadable JSON."""
    config = {
        "currency": st.session_state.currency,
        "levels": st.session_state.levels_data,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    return json.dumps(config, indent=2)

def load_configuration(config_json: str) -> bool:
    """Load configuration from JSON string."""
    try:
        config = json.loads(config_json)
        st.session_state.currency = config.get("currency", "$")
        st.session_state.levels_data = config.get("levels", [])
        return True
    except (json.JSONDecodeError, KeyError):
        return False

# ═══════════════════════════════════════════════════════════════════════════════════
# Main Application
# ═══════════════════════════════════════════════════════════════════════════════════

def main():
    """Main application logic."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎰 Enhanced Mystery Jackpot Calculator</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Currency selection
        currency_options = ["$", "€", "£", "¥", "₹", "Custom"]
        currency_choice = st.selectbox("Currency Symbol", currency_options, 
                                     index=currency_options.index(st.session_state.currency) 
                                     if st.session_state.currency in currency_options else 0)
        
        if currency_choice == "Custom":
            st.session_state.currency = st.text_input("Custom Currency Symbol", 
                                                    value=st.session_state.currency)
        else:
            st.session_state.currency = currency_choice
        
        st.divider()
        
        # Configuration management
        st.subheader("💾 Save/Load Configuration")
        
        if st.button("💾 Export Configuration"):
            config_json = save_configuration()
            st.download_button(
                label="⬇️ Download Config",
                data=config_json,
                file_name="jackpot_config.json",
                mime="application/json"
            )
        
        uploaded_config = st.file_uploader("📁 Upload Configuration", type="json")
        if uploaded_config:
            config_content = uploaded_config.read().decode()
            if load_configuration(config_content):
                st.success("✅ Configuration loaded successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid configuration file")
        
        st.divider()
        
        # Advanced options
        st.session_state.show_advanced = st.checkbox("🔧 Show Advanced Options", 
                                                   value=st.session_state.show_advanced)
    
    # Level Management
    col_info, col_add, col_remove = st.columns([2, 1, 1])
    
    with col_info:
        st.info(f"📊 Managing {len(st.session_state.levels_data)} jackpot level(s)")
    
    with col_add:
        if st.button("➕ Add Level", use_container_width=True):
            st.session_state.levels_data.append({
                "coin": "", "init": "", "min": "", "max": "", "pct": "0.00"
            })
            st.rerun()
    
    with col_remove:
        can_remove = len(st.session_state.levels_data) > 1
        if st.button("➖ Remove Last", disabled=not can_remove, use_container_width=True):
            st.session_state.levels_data.pop()
            st.rerun()
    
    st.divider()
    
    # Input Section
    st.header("📝 Jackpot Level Configuration")
    
    levels = []
    validation_errors = []
    
    # Column headers
    header_cols = st.columns([1, 2, 2, 2, 2, 1.5, 1], gap="small")
    headers = ["#", "Daily Coin-In", "Initial Jackpot", "Min Hit Amount", 
               "Max Hit Amount", "Contribution %", "Status"]
    
    for i, (col, header) in enumerate(zip(header_cols, headers)):
        col.markdown(f"**{header}**")
    
    # Input rows
    for idx, level_data in enumerate(st.session_state.levels_data):
        cols = st.columns([1, 2, 2, 2, 2, 1.5, 1], gap="small")
        
        # Level number
        cols[0].markdown(f"**L{idx + 1}**")
        
        # Input fields
        with cols[1]:
            level_data["coin"] = st.text_input(
                f"Coin-In L{idx + 1}", 
                value=level_data["coin"], 
                key=f"coin_{idx}",
                placeholder="e.g., 1.000.000",
                label_visibility="collapsed"
            )
        
        with cols[2]:
            level_data["init"] = st.text_input(
                f"Initial L{idx + 1}",
                value=level_data["init"],
                key=f"init_{idx}",
                placeholder="e.g., 500.000",
                label_visibility="collapsed"
            )
        
        with cols[3]:
            level_data["min"] = st.text_input(
                f"Min L{idx + 1}",
                value=level_data["min"],
                key=f"min_{idx}",
                placeholder="e.g., 1.000.000",
                label_visibility="collapsed"
            )
        
        with cols[4]:
            level_data["max"] = st.text_input(
                f"Max L{idx + 1}",
                value=level_data["max"],
                key=f"max_{idx}",
                placeholder="e.g., 2.000.000",
                label_visibility="collapsed"
            )
        
        with cols[5]:
            level_data["pct"] = st.text_input(
                f"% L{idx + 1}",
                value=level_data["pct"],
                key=f"pct_{idx}",
                placeholder="e.g., 1.50",
                label_visibility="collapsed"
            )
        
        # Parse and validate data
        coin_in = NumberFormatter.parse_number(level_data["coin"])
        initial_jp = NumberFormatter.parse_number(level_data["init"])
        min_hit = NumberFormatter.parse_number(level_data["min"])
        max_hit = NumberFormatter.parse_number(level_data["max"])
        
        try:
            contribution_pct = float(level_data["pct"].replace(",", "."))
        except ValueError:
            contribution_pct = 0.0
        
        # Apply business rule: use initial as min if min is zero
        if initial_jp > 0 and min_hit == 0:
            min_hit = initial_jp
        
        # Ensure max >= min
        if max_hit < min_hit:
            max_hit = min_hit
        
        # Create level object and validate
        level = JackpotLevel(
            level=idx + 1,
            coin_in=coin_in,
            initial_jp=initial_jp,
            min_hit=min_hit,
            max_hit=max_hit,
            contribution_pct=contribution_pct
        )
        
        is_valid, errors = level.is_valid
        
        # Status indicator
        with cols[6]:
            if is_valid:
                st.success("✅", help="Valid configuration")
            else:
                st.error("❌", help=f"Errors: {'; '.join(errors)}")
                validation_errors.extend([f"Level {idx + 1}: {err}" for err in errors])
        
        levels.append(level)
    
    # Display validation errors
    if validation_errors:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("⚠️ **Configuration Issues Found:**")
        for error in validation_errors:
            st.write(f"• {error}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Results Section
    if levels and not validation_errors:
        st.header("📊 Analysis Results")
        
        # Summary metrics
        total_raw_pct = sum(lvl.contribution_pct for lvl in levels)
        total_effective_pct = sum(lvl.effective_percentage for lvl in levels)
        total_daily_contribution = sum(lvl.daily_contribution for lvl in levels)
        avg_hit_frequency = sum(lvl.hit_frequency_days for lvl in levels if lvl.hit_frequency_days != float('inf')) / len([lvl for lvl in levels if lvl.hit_frequency_days != float('inf')]) if any(lvl.hit_frequency_days != float('inf') for lvl in levels) else 0
        
        # Metrics display
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.markdown(f'''
            <div class="metric-card">
                <h3>Total Raw %</h3>
                <h2>{NumberFormatter.format_percentage(total_raw_pct)}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with metric_cols[1]:
            st.markdown(f'''
            <div class="metric-card">
                <h3>Total Effective %</h3>
                <h2>{NumberFormatter.format_percentage(total_effective_pct)}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with metric_cols[2]:
            st.markdown(f'''
            <div class="metric-card">
                <h3>Daily Contribution</h3>
                <h2>{NumberFormatter.format_currency(total_daily_contribution, st.session_state.currency)}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with metric_cols[3]:
            st.markdown(f'''
            <div class="metric-card">
                <h3>Avg Hit Frequency</h3>
                <h2>{avg_hit_frequency:.1f} days</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        st.divider()
        
        # Detailed table
        st.subheader("📋 Detailed Level Analysis")
        
        table_data = []
        for lvl in levels:
            hit_freq_display = f"{lvl.hit_frequency_days:.2f}" if lvl.hit_frequency_days != float('inf') else "∞"
            
            table_data.append({
                "Level": f"L{lvl.level}",
                "Daily Coin-In": NumberFormatter.format_currency(lvl.coin_in, st.session_state.currency),
                "Initial JP": NumberFormatter.format_currency(lvl.initial_jp, st.session_state.currency),
                "Min Hit": NumberFormatter.format_currency(lvl.min_hit, st.session_state.currency),
                "Max Hit": NumberFormatter.format_currency(lvl.max_hit, st.session_state.currency),
                "Avg Hit": NumberFormatter.format_currency(lvl.avg_hit, st.session_state.currency),
                "Build Amount": NumberFormatter.format_currency(lvl.build_amount, st.session_state.currency),
                "Raw %": NumberFormatter.format_percentage(lvl.contribution_pct),
                "Effective %": NumberFormatter.format_percentage(lvl.effective_percentage),
                "Daily Contribution": NumberFormatter.format_currency(lvl.daily_contribution, st.session_state.currency),
                "Hit Frequency (Days)": hit_freq_display
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export table
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Export Table as CSV",
            data=csv_data,
            file_name="jackpot_analysis.csv",
            mime="text/csv"
        )
        
        # Charts Section
        st.header("📈 Visual Analysis")
        
        ChartGenerator.setup_style()
        
        # Chart tabs
        chart_tabs = st.tabs(["🔄 Comparison Overview", "📊 Individual Metrics", "⚙️ Advanced Charts"])
        
        with chart_tabs[0]:
            # Comprehensive comparison chart
            comp_fig = ChartGenerator.create_comparison_chart(levels)
            st.pyplot(comp_fig)
            
            # Export comprehensive chart
            buf = BytesIO()
            comp_fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
            st.download_button(
                "⬇️ Download Comparison Chart",
                buf.getvalue(),
                "jackpot_comparison.png",
                "image/png"
            )
        
        with chart_tabs[1]:
            # Individual metric charts
            level_nums = [lvl.level for lvl in levels]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Raw vs Effective percentage
                raw_fig = ChartGenerator.create_bar_chart(
                    level_nums,
                    [lvl.contribution_pct for lvl in levels],
                    "Raw Contribution Percentage",
                    "Level",
                    "Percentage (%)",
                    "Blues"
                )
                st.pyplot(raw_fig)
                
                # Hit frequency
                hit_days = [lvl.hit_frequency_days if lvl.hit_frequency_days != float('inf') else 0 for lvl in levels]
                freq_fig = ChartGenerator.create_bar_chart(
                    level_nums,
                    hit_days,
                    "Hit Frequency (Days)",
                    "Level",
                    "Days",
                    "Reds"
                )
                st.pyplot(freq_fig)
            
            with col2:
                # Effective percentage
                eff_fig = ChartGenerator.create_bar_chart(
                    level_nums,
                    [lvl.effective_percentage for lvl in levels],
                    "Effective Contribution Percentage",
                    "Level",
                    "Percentage (%)",
                    "Greens"
                )
                st.pyplot(eff_fig)
                
                # Daily contribution
                contrib_fig = ChartGenerator.create_bar_chart(
                    level_nums,
                    [lvl.daily_contribution for lvl in levels],
                    f"Daily Contribution ({st.session_state.currency})",
                    "Level",
                    f"Amount ({st.session_state.currency})",
                    "Oranges"
                )
                st.pyplot(contrib_fig)
        
        with chart_tabs[2]:
            if st.session_state.show_advanced:
                st.subheader("🔬 Advanced Analytics")
                
                # ROI Analysis
                st.write("**Return on Investment Analysis:**")
                roi_data = []
                for lvl in levels:
                    if lvl.daily_contribution > 0:
                        annual_contribution = lvl.daily_contribution * 365
                        roi_pct = (lvl.build_amount / annual_contribution) * 100 if annual_contribution > 0 else 0
                        roi_data.append({
                            "Level": f"L{lvl.level}",
                            "Annual Contribution": NumberFormatter.format_currency(annual_contribution, st.session_state.currency),
                            "Build Amount": NumberFormatter.format_currency(lvl.build_amount, st.session_state.currency),
                            "ROI (%)": f"{roi_pct:.2f}%"
                        })
                
                if roi_data:
                    st.dataframe(pd.DataFrame(roi_data), use_container_width=True, hide_index=True)
                
                # Sensitivity analysis placeholder
                st.write("**Sensitivity Analysis:**")
                st.info("Advanced sensitivity analysis features can be added here for premium users.")
            else:
                st.info("💡 Enable 'Show Advanced Options' in the sidebar to access advanced analytics.")

if __name__ == "__main__":
    main()
