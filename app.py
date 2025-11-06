import streamlit as st
import requests
import json
import time
import plotly.graph_objects as go
from datetime import datetime

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="CIM-10 Code Suggester",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .suggestion-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .code-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .login-box {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin-top: 5rem;
    }
</style>
""", unsafe_allow_html=True)


if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0


def login(username: str, password: str) -> bool:
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data['access_token']
            st.session_state.username = username
            return True
        else:
            return False
    
    except Exception as e:
        st.error(f"Erreur de connexion: {str(e)}")
        return False


def logout():
    st.session_state.token = None
    st.session_state.username = None
    st.rerun()


def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def suggest_codes(query: str, top_k: int = 5, use_reranking: bool = True):
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{API_URL}/suggest-codes",
            json={
                "query": query,
                "top_k": top_k,
                "use_reranking": use_reranking
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 401:
            st.error("🔒 Session expirée. Veuillez vous reconnecter.")
            logout()
            return None
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur API: {str(e)}")
        return None


def lookup_code(code: str):
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{API_URL}/lookup-code",
            json={"code": code},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            st.error("🔒 Session expirée. Veuillez vous reconnecter.")
            logout()
            return None
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur API: {str(e)}")
        return None


def display_suggestion(suggestion, rank):
    with st.container():
        st.markdown(f"""
        <div class="suggestion-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <span style="font-size: 1.5rem; font-weight: bold;">#{rank}</span>
                    <span class="code-badge">{suggestion['code']}</span>
                </div>
                <div class="relevance-score" style="color: {'green' if suggestion['relevance_score'] > 0.8 else 'orange'};">
                    Score: {suggestion['relevance_score']:.0%}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**{suggestion['label']}**")
        
        # Explanation
        with st.expander("📝 Explication", expanded=True):
            st.write(suggestion['explanation'])
        
        # CoCoA Rules
        col1, col2 = st.columns(2)
        
        with col1:
            if suggestion.get('exclusions'):
                with st.expander(f"❌ Exclusions ({len(suggestion['exclusions'])})"):
                    for excl in suggestion['exclusions']:
                        st.markdown(f"- {excl}")
        
        with col2:
            if suggestion.get('inclusions'):
                with st.expander(f"✅ Inclusions ({len(suggestion['inclusions'])})"):
                    for incl in suggestion['inclusions']:
                        st.markdown(f"- {incl}")
        
        if suggestion.get('coding_instructions'):
            with st.expander("📋 Instructions de codage"):
                for instr in suggestion['coding_instructions']:
                    st.info(instr)
        
        meta_cols = st.columns(3)
        with meta_cols[0]:
            if suggestion.get('chapter'):
                st.caption(f"📚 Chapitre: {suggestion['chapter']}")
        with meta_cols[1]:
            if suggestion.get('priority'):
                st.caption(f"⚡ Priorité: {suggestion['priority']}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")


def login_page():
    """Display login page."""
    st.markdown('<h1 class="main-header">🏥 Système RAG - CIM-10</h1>', unsafe_allow_html=True)
    
    # Check API
    api_status = check_api_health()
    
    if not api_status:
        st.error("❌ API non disponible")
        st.info("Démarrez l'API avec: `python -m src.api.main`")
        st.stop()
    
    st.markdown("""
    <div class="login-box">
        <h2 style="text-align: center; margin-bottom: 2rem;">🔐 Connexion</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", placeholder="admin ou doctor")
            password = st.text_input("🔑 Mot de passe", type="password", placeholder="Mot de passe")
            
            submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            
            if submitted:
                if not username or not password:
                    st.error("Veuillez remplir tous les champs")
                else:
                    with st.spinner("Connexion en cours..."):
                        if login(username, password):
                            st.success("✅ Connexion réussie!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Identifiants incorrects")
        
        # Default credentials info
        with st.expander("ℹ️ Identifiants par défaut"):
            st.info("""
            **Admin:**
            - Username: `admin`
            - Password: `admin`
            """)


def main_app():
    """Main application (after login)."""
    
    st.markdown('<h1 class="main-header">🏥 Système RAG - Suggestion de Codes CIM-10</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/health-book.png", width=100)
        
        st.success(f"👤 Connecté: **{st.session_state.username}**")
        
        if st.button("🚪 Se déconnecter", use_container_width=True):
            logout()
        
        st.markdown("---")
        st.title("⚙️ Configuration")
        
        st.success("✅ API connectée")
        
        st.markdown("---")
        
        st.subheader("Paramètres de recherche")
        top_k = st.slider("Nombre de suggestions", 1, 10, 5)
        use_reranking = st.checkbox("Utiliser le re-ranking LLM", value=True, help="Plus précis mais plus lent")
        
        st.markdown("---")
        
        st.subheader("📊 Statistiques")
        st.metric("Requêtes totales", st.session_state.total_queries)
        
        if st.session_state.query_history:
            avg_time = sum(q['time'] for q in st.session_state.query_history) / len(st.session_state.query_history)
            st.metric("Temps moyen", f"{avg_time:.1f}s")
        
        st.markdown("---")
        
        st.subheader("💡 Exemples rapides")
        examples = [
            "Dyspnée à l'effort",
            "Pneumopathie à Haemophilus",
            "Sepsis à staphylocoques",
            "Insuffisance respiratoire aiguë",
            "Fièvre et toux"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                st.session_state.current_query = example
    
    tab1, tab2, tab3 = st.tabs(["🔍 Recherche", "🔎 Lookup Code", "📈 Historique"])
    
    with tab1:
        st.subheader("Décrivez le symptôme, diagnostic ou pathologie")
        
        query = st.text_area(
            "Requête médicale",
            value=st.session_state.get('current_query', ''),
            height=100,
            placeholder="Ex: Patient présentant une dyspnée à l'effort avec toux productive..."
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_button = st.button("🔍 Suggérer des codes", type="primary", use_container_width=True)
        
        with col2:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                st.session_state.current_query = ""
                st.rerun()
        
        if search_button and query.strip():
            with st.spinner("🤖 Analyse en cours..."):
                start_time = time.time()
                result = suggest_codes(query, top_k, use_reranking)
                elapsed_time = time.time() - start_time
                
                if result:
                    st.session_state.total_queries += 1
                    st.session_state.query_history.append({
                        'query': query,
                        'time': elapsed_time,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'suggestions': len(result['suggestions'])
                    })
                    
                    st.success(f"✅ {len(result['suggestions'])} suggestions trouvées")
                    
                    for i, suggestion in enumerate(result['suggestions'], 1):
                        display_suggestion(suggestion, i)
        
        elif search_button:
            st.warning("⚠️ Veuillez entrer une requête")
    
    with tab2:
        st.subheader("Rechercher un code CIM-10 spécifique")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            code_input = st.text_input("Code CIM-10", placeholder="Ex: A41.0")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            lookup_button = st.button("🔎 Rechercher", type="primary", use_container_width=True)
        
        if lookup_button and code_input:
            with st.spinner("Recherche en cours..."):
                result = lookup_code(code_input.upper())
                
                if result and result.get('found'):
                    st.success(f"✅ Code {result['code']} trouvé")
                    st.text_area("Contenu", result['document'], height=400)
                elif result:
                    st.error(f"❌ {result.get('message', 'Code non trouvé')}")
    
    with tab3:
        st.subheader("📈 Historique des requêtes")
        
        if st.session_state.query_history:
            for i, query in enumerate(reversed(st.session_state.query_history[-20:]), 1):
                with st.expander(f"{i}. {query['timestamp']} - {query['query'][:50]}..."):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Temps", f"{query['time']:.2f}s")
                    with col2:
                        st.metric("Suggestions", query['suggestions'])
        else:
            st.info("📭 Aucune requête dans l'historique")


def main():
    if st.session_state.token is None:
        login_page()
    else:
        main_app()


if __name__ == "__main__":
    main()