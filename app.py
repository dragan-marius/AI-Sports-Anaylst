import streamlit as st
import os 
from dotenv import load_dotenv
from predictor import predict_match
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent

load_dotenv()
GEMINI_KEY =  os.getenv("GEMINI_API_KEY")

@tool
def predict_math_prompt(team_A:str, team_B:str)->str:
    """
    Folosește această unealtă OBLIGATORIU când utilizatorul cere o predicție pentru un meci.
    Input-ul trebuie să fie numele echipelor în engleză. Returnează cotele calculate.
    """
    return predict_match(team_A, team_B)

SYSTEM_PROMPT= """
Ești un Expert în Data Science și Analist Sportiv Predictiv. Când un utilizator îți cere o predicție:
1. Folosește OBLIGATORIU unealta 'predict_math_prompt' pentru a obține cotele și xG-ul.
2. Analizează cotele obținute. Nu oferi doar cifrele reci.
3. Transformă matematica într-o poveste captivantă. Argumentează de ce o cotă este mai mică sau mai mare bazat pe xG.
4. Oferă la final o predicție clară și recomandă un 'Value Bet' (un pariu valoros).
Scrie ca un jurnalist sportiv de top.
"""

llm = ChatGoogleGenerativeAI (
    model = "gemini-2.5-flash",
    google_api_key = GEMINI_KEY,
    temperature= 0.7
)

tools = [predict_math_prompt]

agent = create_agent(
    model=llm, 
    tools=tools, 
    system_prompt=SYSTEM_PROMPT
)

st.set_page_config(page_title="AI Sports Analyst", page_icon="⚽",layout="centered",)
st.title("⚽ AI Sports Analyst")
st.write("Aplicație de predicții sportive bazată pe modele statistice Poisson și Inteligență Artificială.")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    team1 = st.text_input("Echipa 1", value="France")
with col2:
    team2 = st.text_input("Echipa 2", value="Argentina")

if st.button("Analizează Meciul 🚀", use_container_width=True):
    with st.spinner("Motorul matematic calculează cotele, iar AI-ul redactează analiza..."):
        try:
            user_prompt=f"Fă-mi o predicție completă pentru meciul {team1} vs {team2}"
            response = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
            final_answer = response["messages"][-1].content
            if isinstance(final_answer, list):
                final_answer = "".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in final_answer])
            
            st.success("Analiza a fost generata cu succes")
            st.markdown(final_answer)
        except Exception as e:
            st.error(f"A aparut o eroare la generare: {e}")
