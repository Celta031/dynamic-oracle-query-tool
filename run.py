from app import create_app

app = create_app()

if __name__ == "__main__":
    # O 'debug=True' reinicia o servidor automaticamente
    # quando você salva uma alteração no código.
    # NUNCA use debug=True em produção.
    app.run(host='0.0.0.0', port=5000, debug=True)