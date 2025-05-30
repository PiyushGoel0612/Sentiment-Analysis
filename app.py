import streamlit as st
import requests
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="News Analysis Dashboard",
    page_icon="📰",
    layout="wide"
)

# Initialize session state
if 'analyzed_data' not in st.session_state:
    st.session_state.analyzed_data = None
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = ""
if 'loading' not in st.session_state:
    st.session_state.loading = False

# Function to fetch data from API
def fetch_data(topic):
    url = "https://mudfish-glorious-jackal.ngrok-free.app/analyze/"
    try:
        response = requests.post(url, json={"topic": topic})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None

# Function to extract sentiment as string
def extract_sentiment(sentiment_data):
    """Extract sentiment string from various data formats"""
    if isinstance(sentiment_data, str):
        return sentiment_data.lower()
    elif isinstance(sentiment_data, dict):
        # Handle your API format: {'label': 'POSITIVE', 'score': 0.99}
        if 'label' in sentiment_data:
            label = str(sentiment_data['label']).lower()
            # Convert POSITIVE/NEGATIVE to positive/negative
            if label in ['positive', 'negative']:
                return label
            elif label == 'label_1':
                return 'positive'
            elif label == 'label_0':
                return 'negative'
            else:
                return label
        elif 'sentiment' in sentiment_data:
            return str(sentiment_data['sentiment']).lower()
        elif 'prediction' in sentiment_data:
            return str(sentiment_data['prediction']).lower()
        else:
            # Return the first value if it's a simple key-value pair
            return str(list(sentiment_data.values())[0]).lower() if sentiment_data else 'unknown'
    else:
        return str(sentiment_data).lower() if sentiment_data else 'unknown'

# Function to extract sentiment score
def extract_sentiment_score(sentiment_data):
    """Extract sentiment confidence score"""
    if isinstance(sentiment_data, dict) and 'score' in sentiment_data:
        return float(sentiment_data['score'])
    return 0.0

# Function to create sentiment color mapping
def get_sentiment_color(sentiment):
    sentiment = sentiment.lower() if sentiment else 'unknown'
    color_map = {
        'positive': '#28a745',
        'negative': '#dc3545', 
        'neutral': '#6c757d',
        'mixed': '#fd7e14',
        'unknown': '#6c757d'
    }
    return color_map.get(sentiment, '#6c757d')

# Sidebar navigation
st.sidebar.title("📰 News Analysis Dashboard")
st.sidebar.markdown("---")

# Show current topic in sidebar if available
if st.session_state.current_topic:
    st.sidebar.success(f"**Current Topic:** {st.session_state.current_topic}")
    if st.session_state.analyzed_data:
        # Handle both old and new data formats
        if isinstance(st.session_state.analyzed_data, list):
            # Direct list format from your JSON
            article_count = len(st.session_state.analyzed_data)
        else:
            # Dictionary format with 'results' key
            article_count = len(st.session_state.analyzed_data.get('results', []))
        st.sidebar.markdown(f"**Articles Found:** {article_count}")
    st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate to:",
    ["🏠 Home", "📊 Sentiment Analysis", "📋 Article Summaries"],
    index=0
)

# HOME PAGE
if page == "🏠 Home":
    st.title("🏠 News Summary & Sentiment Viewer")
    st.markdown("Enter a topic to analyze news articles and their sentiment.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        topic = st.text_input(
            "Enter a topic (e.g., Farming, AI, Politics)", 
            value=st.session_state.current_topic,
            placeholder="Type your topic here..."
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if analyze_button and topic:
        st.session_state.loading = True
        
        with st.spinner(f"Analyzing news about '{topic}'..."):
            data = fetch_data(topic)
            
            if data:
                st.session_state.analyzed_data = data
                st.session_state.current_topic = topic
                # Handle both data formats
                if isinstance(data, list):
                    article_count = len(data)
                else:
                    article_count = len(data.get('results', []))
                st.success(f"✅ Analysis complete! Found {article_count} articles.")
                st.rerun()
            
        st.session_state.loading = False

    # Display results if available
    if st.session_state.analyzed_data:
        data = st.session_state.analyzed_data
        
        # Handle both data formats - list or dict with 'results' key
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", [])
        
        if results:
            st.markdown("---")
            st.subheader(f"📈 Quick Overview - {st.session_state.current_topic}")
            
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Articles", len(results))
            
            sentiments = [extract_sentiment(result.get('sentiment', 'Unknown')) for result in results]
            sentiment_counts = pd.Series(sentiments).value_counts()
            
            with col2:
                positive_count = sentiment_counts.get('positive', 0)
                st.metric("Positive", positive_count)
            
            with col3:
                negative_count = sentiment_counts.get('negative', 0)
                st.metric("Negative", negative_count)
            
            with col4:
                neutral_count = sentiment_counts.get('neutral', 0)
                st.metric("Neutral", neutral_count)
            
            # Recent articles preview
            st.markdown("---")
            st.subheader("📰 Recent Articles Preview")
            
            for i, result in enumerate(results[:3], start=1):  # Show only first 3
                with st.expander(f"Article {i} - {extract_sentiment(result.get('sentiment', 'Unknown')).title()} Sentiment"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Display title if available
                        title = result.get('title', f'Article {i}')
                        st.write(f"**Title**: {title}")
                        st.write(f"**Summary**: {result.get('summary', 'N/A')}")
                        link = result.get("url") or result.get("link")  # Handle both url and link keys
                        if link:
                            st.markdown(f"🔗 [Read Full Article]({link})")
                    
                    with col2:
                        sentiment_data = result.get('sentiment', {})
                        sentiment = extract_sentiment(sentiment_data)
                        score = extract_sentiment_score(sentiment_data)
                        color = get_sentiment_color(sentiment)
                        
                        st.markdown(f'<div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; text-align: center;"><b>{sentiment.title()}</b><br><small>Confidence: {score:.2f}</small></div>', unsafe_allow_html=True)
            
            if len(results) > 3:
                st.info(f"📋 View all {len(results)} articles in the 'Article Summaries' page")
        else:
            st.warning("No results found for this topic.")

# SENTIMENT ANALYSIS PAGE
elif page == "📊 Sentiment Analysis":
    st.title("📊 Sentiment Analysis Dashboard")
    
    if st.session_state.analyzed_data:
        data = st.session_state.analyzed_data
        
        # Handle both data formats
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", [])
        
        if results:
            st.markdown(f"**Analyzing sentiment for:** {st.session_state.current_topic}")
            st.markdown("---")
            
            # Prepare data
            sentiments = [extract_sentiment(result.get('sentiment', 'Unknown')) for result in results]
            summaries = [result.get('summary', 'N/A')[:100] + '...' for result in results]
            
            # Create DataFrame
            df = pd.DataFrame({
                'Article': [f"Article {i+1}" for i in range(len(results))],
                'Sentiment': sentiments,
                'Confidence': [extract_sentiment_score(result.get('sentiment', {})) for result in results],
                'Summary_Preview': summaries
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Overall Sentiment Distribution")
                sentiment_counts = pd.Series(sentiments).value_counts().reset_index()
                sentiment_counts.columns = ['Sentiment', 'Count']
                
                # Create pie chart
                fig_pie = px.pie(
                    sentiment_counts, 
                    values='Count', 
                    names='Sentiment',
                    title="Sentiment Distribution",
                    color_discrete_map={
                        'positive': '#28a745',
                        'negative': '#dc3545', 
                        'neutral': '#6c757d',
                        'mixed': '#fd7e14'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("📈 Sentiment by Article")
                
                # Create bar chart
                fig_bar = px.bar(
                    df, 
                    x='Article', 
                    color='Sentiment',
                    title="Individual Article Sentiments",
                    color_discrete_map={
                        'positive': '#28a745',
                        'negative': '#dc3545', 
                        'neutral': '#6c757d',
                        'mixed': '#fd7e14'
                    }
                )
                fig_bar.update_layout(showlegend=True, xaxis_tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Detailed breakdown
            st.markdown("---")
            st.subheader("📋 Detailed Sentiment Breakdown")
            
            # Create tabs for different sentiment categories
            unique_sentiments = sentiment_counts['Sentiment'].unique()
            sentiment_tabs = st.tabs(["All Articles"] + [s.title() for s in unique_sentiments])
            
            with sentiment_tabs[0]:
                st.dataframe(
                    df[['Article', 'Sentiment', 'Confidence', 'Summary_Preview']], 
                    use_container_width=True,
                    hide_index=True
                )
            
            for i, sentiment_type in enumerate(unique_sentiments, 1):
                with sentiment_tabs[i]:
                    filtered_df = df[df['Sentiment'] == sentiment_type]
                    if not filtered_df.empty:
                        st.dataframe(
                            filtered_df[['Article', 'Sentiment', 'Confidence', 'Summary_Preview']], 
                            use_container_width=True,
                            hide_index=True
                        )
                        # Show average confidence for this sentiment
                        avg_confidence = filtered_df['Confidence'].mean()
                        st.info(f"Average confidence for {sentiment_type} articles: {avg_confidence:.3f}")
                    else:
                        st.info(f"No {sentiment_type} articles found.")
        else:
            st.warning("No data available for sentiment analysis.")
    else:
        st.info("📝 Please go to the Home page and analyze a topic first to view sentiment analysis.")

# ARTICLE SUMMARIES PAGE
elif page == "📋 Article Summaries":
    st.title("📋 Article Summaries")
    
    if st.session_state.analyzed_data:
        data = st.session_state.analyzed_data
        
        # Handle both data formats
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", [])
        
        if results:
            st.markdown(f"**Topic:** {st.session_state.current_topic}")
            st.markdown(f"**Total Articles:** {len(results)}")
            st.markdown("---")
            
            # Search and filter options
            col1, col2 = st.columns([2, 1])
            
            with col1:
                search_term = st.text_input("🔍 Search in summaries", placeholder="Enter keywords to search...")
            
            with col2:
                # Fixed: Extract sentiments properly and get unique values
                all_sentiments = [extract_sentiment(s.get('sentiment', 'Unknown')) for s in results]
                unique_sentiments = list(set(all_sentiments))
                sentiment_options = ["All"] + [s.title() for s in unique_sentiments]
                
                sentiment_filter = st.selectbox(
                    "Filter by Sentiment",
                    options=sentiment_options
                )
            
            # Filter results
            filtered_results = results
            
            if search_term:
                filtered_results = [
                    r for r in filtered_results 
                    if search_term.lower() in r.get('summary', '').lower() or 
                       search_term.lower() in r.get('title', '').lower()
                ]
            
            if sentiment_filter != "All":
                filtered_results = [
                    r for r in filtered_results 
                    if extract_sentiment(r.get('sentiment', 'Unknown')).title() == sentiment_filter
                ]
            
            st.markdown(f"**Showing {len(filtered_results)} of {len(results)} articles**")
            st.markdown("---")
            
            # Display articles in card format
            for i, result in enumerate(filtered_results, start=1):
                with st.container():
                    # Card-like styling
                    sentiment_data = result.get('sentiment', {})
                    sentiment = extract_sentiment(sentiment_data)
                    score = extract_sentiment_score(sentiment_data)
                    color = get_sentiment_color(sentiment)
                    
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin: 10px 0; background-color: #f9f9f9;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="margin: 0; color: #333;">📰 Article {i}</h3>
                            <div style="text-align: center;">
                                <span style="background-color: {color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: block;">
                                    {sentiment.title()}
                                </span>
                                <small style="color: #666; margin-top: 5px; display: block;">Confidence: {score:.3f}</small>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Title if available
                    title = result.get('title', f'Article {i}')
                    if title and title != f'Article {i}':
                        st.markdown(f"**📝 Title:** {title}")
                    
                    # Summary
                    summary = result.get('summary', 'No summary available')
                    st.markdown(f"**📄 Summary:** {summary}")
                    
                    # Link - handle both 'url' and 'link' keys
                    link = result.get("url") or result.get("link")
                    if link:
                        st.markdown(f"**🔗 Source:** [Read Full Article]({link})")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            if not filtered_results:
                st.warning("No articles match your search criteria.")
        else:
            st.warning("No articles found.")
    else:
        st.info("📝 Please go to the Home page and analyze a topic first to view article summaries.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>📰 News Analysis Dashboard | Built with Streamlit</p>
    </div>
    """, 
    unsafe_allow_html=True
)