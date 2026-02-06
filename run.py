from app.Flask_app.app import create_app

app = create_app()

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
