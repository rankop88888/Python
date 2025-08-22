# ═══════════════════════════════════════════════════════════════════════════════════
#  Enhanced Mystery Jackpot Contribution Calculator  •  v3.0
#  Advanced gaming industry tool for jackpot contribution analysis
# ═══════════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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
    margin: 0.5rem 0;
    text-align: center;
}
.metric-card h3 {
    margin: 0;
    font-size: 1rem;
    opacity: 0.9;
}
.metric-card h2 {
    margin: 0.5rem 0 0 0;
    font-size: 1.8rem;
    font-weight: bold;
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
.status-valid {
    color: #28a745;
    font-weight: bold;
}
.status-invalid {
    color: #dc3545;
    font-weight: bold;
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
        if self.min_hit > 0 and self.min_hit < self.initial_jp:
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
        if amount == float('inf'):
            return "∞"
        formatted = f"{int(round(amount)):,}".replace(",", ".")
        return f"{formatted} {currency}".strip()
    
    @staticmethod
    def format_percentage(pct: float, decimals: int = 2) -> str:
        """Format percentage with specified decimal places."""
        return f"{pct:.{decimals}f}%"

class ChartGenerator:
    """Generate enhanced charts with consistent styling."""
    
    # Color palettes without seaborn dependency
    COLORS = {
        'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'],
        'blues': ['#08519c', '#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#deebf7', '#f7fbff'],
        'greens': ['#00441b', '#238b45', '#41ab5d', '#74c476', '#a1d99b', '#c7e9c0', '#e5f5e0'],
        'reds': ['#67000d', '#a50f15', '#cb181d', '#ef3b2c', '#fb6a4a', '#fc9272', '#fcbba1'],
        'oranges': ['#7f2704', '#a63603', '#cc4c02', '#ec7014', '#fe9929', '#fec44f', '#fee391']
    }
    
    @staticmethod
    def get_color_palette(name: str, n_colors: int) -> List[str]:
        """Get color palette without seaborn dependency."""
        if name.lower() in ChartGenerator.COLORS:
            colors = ChartGenerator.COLORS[name.lower()]
            if len(colors) >= n_colors:
                return colors[:n_colors]
            else:
                # Cycle through colors if we need more
                return [colors[i % len(colors)] for i in range(n_colors)]
        else:
            # Default to primary colors
            colors = ChartGenerator.COLORS['primary']
            return [colors[i % len(colors)] for i in range(n_colors)]
    
    @staticmethod
    def setup_matplotlib():
        """Setup matplotlib styling."""
        plt.style.use('default')
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['axes.edgecolor'] = '#cccccc'
        plt.rcParams['grid.color'] = '#e0e0e0'
        plt.rcParams['text.color'] = '#333333'
        plt.rcParams['axes.labelcolor'] = '#333333'
        plt.rcParams['xtick.color'] = '#333333'
        plt.rcParams['ytick.color'] = '#333333'
        
    @staticmethod
    def create_bar_chart(x_data: List, y_data: List, title: str, 
                        xlabel: str, ylabel: str, color_scheme: str = "primary") -> plt.Figure:
        """Create enhanced bar chart."""
        ChartGenerator.setup_matplotlib()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ChartGenerator.get_color_palette(color_scheme, len(x_data))
        
        bars = ax.bar(x_data, y_data, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12, fontweight='600')
        ax.set_ylabel(ylabel, fontsize=12, fontweight='600')
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Add value labels on bars
        for bar, value in zip(bars, y_data):
            height = bar.get_height()
            if height != float('inf') and height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + max(y_data) * 0.01,
                       f'{height:.1f}', ha='center', va='bottom', 
                       fontweight='bold', fontsize=10)
        
        # Improve layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_comparison_chart(levels: List[JackpotLevel]) -> plt.Figure:
        """Create multi-metric comparison chart."""
        if not levels:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No data to display', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=16)
            return fig
        
        ChartGenerator.setup_matplotlib()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        level_nums = [lvl.level for lvl in levels]
        n_levels = len(level_nums)
        
        # Color schemes for each subplot
        colors1 = ChartGenerator.get_color_palette("blues", n_levels)
        colors2 = ChartGenerator.get_color_palette("reds", n_levels)
        colors3 = ChartGenerator.get_color_palette("greens", n_levels)
        colors4 = ChartGenerator.get_color_palette("oranges", n_levels)
        
        # Raw vs Effective Percentage
        raw_pcts = [lvl.contribution_pct for lvl in levels]
        eff_pcts = [lvl.effective_percentage for lvl in levels]
        
        x = np.arange(len(level_nums))
        width = 0.35
        
        ax1.bar(x - width/2, raw_pcts, width, label='Raw %', color=colors1[0], alpha=0.8)
        ax1.bar(x + width/2, eff_pcts, width, label='Effective %', color=colors1[1], alpha=0.8)
        ax1.set_title('Raw vs Effective Contribution %', fontweight='bold', fontsize=14)
        ax1.set_xlabel('Level', fontweight='600')
        ax1.set_ylabel('Percentage', fontweight='600')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'L{num}' for num in level_nums])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # Hit Frequency
        hit_days = [lvl.hit_frequency_days if lvl.hit_frequency_days != float('inf') else 0 for lvl in levels]
        ax2.bar(level_nums, hit_days, color=colors2, alpha=0.8)
        ax2.set_title('Hit Frequency (Days)', fontweight='bold', fontsize=14)
        ax2.set_xlabel('Level', fontweight='600')
        ax2.set_ylabel('Days', fontweight='600')
        ax2.grid(True, alpha=0.3)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # Daily Contribution
        daily_contribs = [lvl.daily_contribution for lvl in levels]
        ax3.bar(level_nums, daily_contribs, color=colors3, alpha=0.8)
        ax3.set_title('Daily Contribution Amount', fontweight='bold', fontsize=14)
        ax3.set_xlabel('Level', fontweight='600')
        ax3.set_ylabel('Amount', fontweight='600')
        ax3.grid(True, alpha=0.3)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        
        # Average Hit vs Initial
        initial_amounts = [lvl.initial_jp for lvl in levels]
        avg_hits = [lvl.avg_hit for lvl in levels]
        
        ax4.bar(x - width/2, initial_amounts, width, label='Initial JP', color=colors4[0], alpha=0.8)
        ax4.bar(x + width/2, avg_hits, width, label='Avg Hit', color=colors4[1], alpha=0.8)
        ax4.set_title('Initial JP vs Average Hit', fontweight='bold', fontsize=14)
        ax4.set_xlabel('Level', fontweight='600')
        ax4.set_ylabel('Amount', fontweight='600')
        ax4.set_xticks(x)
        ax4.set_xticklabels([f'L{num}' for num in level_nums])
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)
        
        plt.tight_layout(pad=3.0)
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
        st.session_state.currency = " "
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
        st.session_state.currency = config.get("currency", " ")
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
        currency_options = ["ISK","$", "€", "£", "¥", "₹", "Custom"]
        current_currency = st.session_state.currency
        if current_currency in currency_options:
            currency_index = currency_options.index(current_currency)
        else:
            currency_index = currency_options.index("Custom")
            
        currency_choice = st.selectbox("Currency Symbol", currency_options, 
                                     index=currency_index)
        
        if currency_choice == "Custom":
            st.session_state.currency = st.text_input("Custom Currency Symbol", 
                                                    value=current_currency if current_currency not in currency_options[:-1] else "$")
        else:
            st.session_state.currency = currency_choice
        
        st.divider()
        
        # Configuration management
        st.subheader("💾 Save/Load Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Export", use_container_width=True):
                config_json = save_configuration()
                st.download_button(
                    label="⬇️ Download",
                    data=config_json,
                    file_name="jackpot_config.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            uploaded_config = st.file_uploader("📁 Upload", type="json", label_visibility="collapsed")
            
        if uploaded_config:
            try:
                config_content = uploaded_config.read().decode()
                if load_configuration(config_content):
                    st.success("✅ Configuration loaded!")
                    st.rerun()
                else:
                    st.error("❌ Invalid configuration file")
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
        
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
        
        # Input fields with better key management
        level_data["coin"] = cols[1].text_input(
            f"Coin-In L{idx + 1}", 
            value=level_data["coin"], 
            key=f"coin_{idx}_{len(st.session_state.levels_data)}",
            placeholder="e.g., 1.000.000",
            label_visibility="collapsed"
        )
        
        level_data["init"] = cols[2].text_input(
            f"Initial L{idx + 1}",
            value=level_data["init"],
            key=f"init_{idx}_{len(st.session_state.levels_data)}",
            placeholder="e.g., 500.000",
            label_visibility="collapsed"
        )
        
        level_data["min"] = cols[3].text_input(
            f"Min L{idx + 1}",
            value=level_data["min"],
            key=f"min_{idx}_{len(st.session_state.levels_data)}",
            placeholder="e.g., 1.000.000",
            label_visibility="collapsed"
        )
        
        level_data["max"] = cols[4].text_input(
            f"Max L{idx + 1}",
            value=level_data["max"],
            key=f"max_{idx}_{len(st.session_state.levels_data)}",
            placeholder="e.g., 2.000.000",
            label_visibility="collapsed"
        )
        
        level_data["pct"] = cols[5].text_input(
            f"% L{idx + 1}",
            value=level_data["pct"],
            key=f"pct_{idx}_{len(st.session_state.levels_data)}",
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
            if is_valid and any([coin_in, initial_jp, min_hit, max_hit, contribution_pct]):
                st.markdown('<span class="status-valid">✅</span>', unsafe_allow_html=True)
            elif errors:
                st.markdown('<span class="status-invalid">❌</span>', unsafe_allow_html=True)
                validation_errors.extend([f"Level {idx + 1}: {err}" for err in errors])
            else:
                st.markdown("⚪")  # Empty/incomplete
        
        levels.append(level)
    
    # Display validation errors
    if validation_errors:
        with st.expander("⚠️ Configuration Issues", expanded=True):
            for error in validation_errors:
                st.warning(f"• {error}")
    
    # Results Section
    valid_levels = [lvl for lvl in levels if lvl.is_valid[0] and any([lvl.coin_in, lvl.initial_jp, lvl.min_hit, lvl.max_hit, lvl.contribution_pct])]
    
    if valid_levels:
        st.header("📊 Analysis Results")
        
        # Summary metrics
        total_raw_pct = sum(lvl.contribution_pct for lvl in valid_levels)
        total_effective_pct = sum(lvl.effective_percentage for lvl in valid_levels)
        total_daily_contribution = sum(lvl.daily_contribution for lvl in valid_levels)
        
        valid_hit_frequencies = [lvl.hit_frequency_days for lvl in valid_levels if lvl.hit_frequency_days != float('inf')]
        avg_hit_frequency = sum(valid_hit_frequencies) / len(valid_hit_frequencies) if valid_hit_frequencies else 0
        
        # Metrics display
        metric_cols = st.columns(4)
        
        metrics = [
            ("Total Raw %", NumberFormatter.format_percentage(total_raw_pct)),
            ("Total Effective %", NumberFormatter.format_percentage(total_effective_pct)),
            ("Daily Contribution", NumberFormatter.format_currency(total_daily_contribution, st.session_state.currency)),
            ("Avg Hit Frequency", f"{avg_hit_frequency:.1f} days" if avg_hit_frequency > 0 else "N/A")
        ]
        
        for i, (metric_cols, (title, value)) in enumerate(zip(metric_cols, metrics)):
            metric_cols.markdown(f'''
            <div class="metric-card">
                <h3>{title}</h3>
                <h2>{value}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        st.divider()
        
        # Detailed table
        st.subheader("📋 Detailed Level Analysis")
        
        table_data = []
        for lvl in valid_levels:
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
        
        if table_data:
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
        if len(valid_levels) > 0:
            st.header("📈 Visual Analysis")
            
            # Chart tabs
            chart_tabs = st.tabs(["🔄 Comparison Overview", "📊 Individual Metrics"])
            
            with chart_tabs[0]:
                # Comprehensive comparison chart
                try:
                    comp_fig = ChartGenerator.create_comparison_chart(valid_levels)
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
                except Exception as e:
                    st.error(f"Error generating comparison chart: {str(e)}")
            
            with chart_tabs[1]:
                # Individual metric charts
                level_nums = [lvl.level for lvl in valid_levels]
                
                col1, col2 = st.columns(2)
                
                try:
                    with col1:
                        # Raw percentage
                        raw_fig = ChartGenerator.create_bar_chart(
                            level_nums,
                            [lvl.contribution_pct for lvl in valid_levels],
                            "Raw Contribution Percentage",
                            "Level",
                            "Percentage (%)",
                            "blues"
                        )
                        st.pyplot(raw_fig)
                        
                        # Hit frequency
                        hit_days = [lvl.hit_frequency_days if lvl.hit_frequency_days != float('inf') else 0 for lvl in valid_levels]
                        freq_fig = ChartGenerator.create_bar_chart(
                            level_nums,
                            hit_days,
                            "Hit Frequency (Days)",
                            "Level",
                            "Days",
                            "reds"
                        )
                        st.pyplot(freq_fig)
                    
                    with col2:
                        # Effective percentage
                        eff_fig = ChartGenerator.create_bar_chart(
                            level_nums,
                            [lvl.effective_percentage for lvl in valid_levels],
                            "Effective Contribution Percentage",
                            "Level",
                            "Percentage (%)",
                            "greens"
                        )
                        st.pyplot(eff_fig)
                        
                        # Daily contribution
                        contrib_fig = ChartGenerator.create_bar_chart(
                            level_nums,
                            [lvl.daily_contribution for lvl in valid_levels],
                            f"Daily Contribution ({st.session_state.currency})",
                            "Level",
                            f"Amount ({st.session_state.currency})",
                            "oranges"
                        )
                        st.pyplot(contrib_fig)
                
                except Exception as e:
                    st.error(f"Error generating individual charts: {str(e)}")
        
        # Advanced Analytics Section
        if st.session_state.show_advanced and valid_levels:
            st.header("🔬 Advanced Analytics")
            
            # ROI Analysis
            st.subheader("📈 Return on Investment Analysis")
            roi_data = []
            for lvl in valid_levels:
                if lvl.daily_contribution > 0:
                    annual_contribution = lvl.daily_contribution * 365
                    payback_ratio = (lvl.build_amount / annual_contribution) if annual_contribution > 0 else 0
                    roi_data.append({
                        "Level": f"L{lvl.level}",
                        "Annual Contribution": NumberFormatter.format_currency(annual_contribution, st.session_state.currency),
                        "Build Amount": NumberFormatter.format_currency(lvl.build_amount, st.session_state.currency),
                        "Payback Ratio": f"{payback_ratio:.2f} years",
                        "Efficiency Score": f"{(lvl.effective_percentage / max(lvl.contribution_pct, 0.01)) * 100:.1f}%"
                    })
            
            if roi_data:
                roi_df = pd.DataFrame(roi_data)
                st.dataframe(roi_df, use_container_width=True, hide_index=True)
                
                # Export ROI analysis
                roi_csv = roi_df.to_csv(index=False)
                st.download_button(
                    "📊 Export ROI Analysis",
                    roi_csv,
                    "roi_analysis.csv",
                    "text/csv"
                )
            
            # Performance Insights
            st.subheader("💡 Performance Insights")
            
            insights = []
            
            # Find most efficient level
            if valid_levels:
                best_efficiency = max(valid_levels, key=lambda x: x.effective_percentage)
                insights.append(f"🏆 **Most Efficient Level**: L{best_efficiency.level} with {best_efficiency.effective_percentage:.2f}% effective contribution")
                
                # Find fastest hitting level
                fastest_hit = min([lvl for lvl in valid_levels if lvl.hit_frequency_days != float('inf')], 
                                key=lambda x: x.hit_frequency_days, default=None)
                if fastest_hit:
                    insights.append(f"⚡ **Fastest Hit**: L{fastest_hit.level} with {fastest_hit.hit_frequency_days:.1f} days average")
                
                # Find highest daily contribution
                highest_contrib = max(valid_levels, key=lambda x: x.daily_contribution)
                insights.append(f"💰 **Highest Daily Contribution**: L{highest_contrib.level} with {NumberFormatter.format_currency(highest_contrib.daily_contribution, st.session_state.currency)}")
                
                # Check for potential issues
                low_efficiency_levels = [lvl for lvl in valid_levels if lvl.effective_percentage < lvl.contribution_pct * 0.5]
                if low_efficiency_levels:
                    level_names = ", ".join([f"L{lvl.level}" for lvl in low_efficiency_levels])
                    insights.append(f"⚠️ **Low Efficiency Warning**: {level_names} have significantly lower effective percentages")
            
            for insight in insights:
                st.info(insight)
    
    else:
        st.info("👆 Please configure at least one valid jackpot level to see analysis results.")

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em; padding: 2rem 0;">
        🎰 Enhanced Mystery Jackpot Calculator v3.0<br>
        Professional gaming industry analysis tool
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
