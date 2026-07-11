import os
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .predictor import predict_match

# Importurile tale pentru LangChain și Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent

# Încărcăm cheia API
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# 1. Definim unealta pentru AI (exact ca în app.py)
@tool
def predict_math_prompt(team_A: str, team_B: str) -> str:
    """
    Folosește această unealtă OBLIGATORIU când utilizatorul cere o predicție pentru un meci.
    Input-ul trebuie să fie numele echipelor în engleză. Returnează cotele calculate.
    """
    return predict_match(team_A, team_B)

# 2. Configurăm Agentul la nivel global (ca să nu îl reinițializăm la fiecare request)
SYSTEM_PROMPT = """
Ești un Expert în Data Science și Analist Sportiv Predictiv. Când un utilizator îți cere o predicție:
1. Folosește OBLIGATORIU unealta 'predict_math_prompt' pentru a obține cotele și xG-ul.
2. Analizează cotele obținute. Nu oferi doar cifrele reci.
3. Transformă matematica într-o poveste captivantă. Argumentează de ce o cotă este mai mică sau mai mare bazat pe xG.
4. Oferă la final o predicție clară și recomandă un 'Value Bet' (un pariu valoros).
Scrie ca un jurnalist sportiv de top.
"""

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_KEY,
    temperature=0.7
)

tools = [predict_math_prompt]

agent = create_agent(
    model=llm, 
    tools=tools, 
    system_prompt=SYSTEM_PROMPT
)

# 3. Endpoint-ul care primește cererea de la React
@api_view(['POST'])
def get_prediction(request):
    team_a = request.data.get('team_A')
    team_b = request.data.get('team_B')

    if not team_a or not team_b:
        return Response({'error': 'Te rog să introduci ambele echipe.'}, status=400)

    try:
        # 4. Creăm promptul și chemăm inteligența artificială
        user_prompt = f"Fă-mi o predicție completă pentru meciul {team_a} vs {team_b}"
        
        response = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
        
        # Extragem răspunsul curat (exact logica ta de formatare)
        final_answer = response["messages"][-1].content
        if isinstance(final_answer, list):
            final_answer = "".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in final_answer])
        
        # 5. Returnăm și textul generat de AI, și echipele
        return Response({
            'team_A': team_a,
            'team_B': team_b,
            'ai_analysis': final_answer
        })
        
    except Exception as e:
        return Response({'error': f"Eroare la generare AI: {str(e)}"}, status=500)