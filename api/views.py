import os
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .predictor import predict_match

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# 1. Actualizăm unealta ca să accepte noii parametri
@tool
def predict_math_prompt(team_A: str, team_B: str, comp_type: str = "World Cup", manual_stage: str = "Auto") -> str:
    """
    Folosește această unealtă OBLIGATORIU când utilizatorul cere o predicție pentru un meci.
    Input-ul trebuie să fie numele echipelor în engleză. Parametrii comp_type și manual_stage 
    trebuie trimiși exact așa cum ți-au fost ceruți.
    """
    return predict_match(team_A, team_B, comp_type=comp_type, manual_stage=manual_stage)

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

@api_view(['POST'])
def get_prediction(request):
    team_a = request.data.get('team_A')
    team_b = request.data.get('team_B')
    
    # 2. Extragem datele din Simulator (dacă utilizatorul a selectat ceva)
    comp_type = request.data.get('comp_type', 'World Cup')
    manual_stage = request.data.get('manual_stage', 'Auto')

    if not team_a or not team_b:
        return Response({'error': 'Te rog să introduci ambele echipe.'}, status=400)

    try:
        # 3. Construim promptul pentru Gemini, spunându-i să folosească setările primite
        user_prompt = f"Fă-mi o predicție completă pentru meciul {team_a} vs {team_b}. "
        if manual_stage != "Auto" or comp_type != "World Cup":
            user_prompt += f"Folosește setările manuale OBLIGATORII pentru unealta ta: comp_type='{comp_type}', manual_stage='{manual_stage}'."

        response = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
        
        final_answer = response["messages"][-1].content
        if isinstance(final_answer, list):
            final_answer = "".join([str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in final_answer])
        
        return Response({
            'team_A': team_a,
            'team_B': team_b,
            'ai_analysis': final_answer
        })
        
    except Exception as e:
        return Response({'error': f"Eroare la generare AI: {str(e)}"}, status=500)