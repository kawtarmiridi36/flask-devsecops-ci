import os
import sys

# Ajouter le chemin actuel
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()

print("=" * 50)
print("🔍 DIAGNOSTIC APPLICATION FLASK")
print("=" * 50)

# Test des templates
print("\n📁 TEMPLATES DISPONIBLES:")
templates_dir = 'templates'
if os.path.exists(templates_dir):
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                print(f"  ✅ {path}")

# Test des routes
print("\n🛣️ ROUTES ENREGISTRÉES:")
for rule in app.url_map.iter_rules():
    if 'dev' in str(rule) or rule.endpoint in ['health', 'index']:
        print(f"  {rule.endpoint:25} {str(rule):30} {list(rule.methods)}")

# Test de rendu template
print("\n🎯 TEST RENDU TEMPLATES:")
with app.test_client() as client:
    # Test index
    try:
        response = client.get('/')
        print(f"  /     - Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ index.html RENDU AVEC SUCCÈS")
        else:
            print(f"  ❌ Erreur: {response.get_data(as_text=True)[:100]}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")
    
    # Test health
    response = client.get('/health')
    print(f"  /health - Status: {response.status_code}")
    
    # Test dev
    response = client.get('/dev')
    print(f"  /dev    - Status: {response.status_code}")
    
    # Test dev-test
    response = client.get('/dev-test')
    print(f"  /dev-test - Status: {response.status_code}")

print("\n" + "=" * 50)
