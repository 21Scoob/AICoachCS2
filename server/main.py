from fastapi import FastAPI

app = FastAPI()

@app.get('/')
    return{'Hai sal'}