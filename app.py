from flask import Flask, request, redirect, session, render_template_string
import requests
import secrets

# these are some flask things, just ignore
app = Flask(__name__)
app.secret_key = "any-string-here"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# the server you want to authenticate
SERVER_URL = "https://app.speckle.systems"

# app_id and app_secret will be provided to you once you register your app in the server
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"

# a simple html to showcase
HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .button { background: #0096ff; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px 10px 0; }
        .info { background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 10px 0; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Speckle Auth Demo</h1>
        {{ content|safe }}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # check if session stored a token already
    token = session.get('token')

    # if yes, show the information about user using graphql query
    if token:
        r = requests.post(f"{SERVER_URL}/graphql",
            json={"query": "{ activeUser { name email avatar } }"},
            headers={"Authorization": f"Bearer {token}"})
        user = r.json()['data']['activeUser']
        
        # censor token :)
        censored_token = token[:4] + "•" * (len(token) - 4)
        
        content = f"""
        <p>✅ Logged in as <strong>{user['name']}</strong></p>
        <p>Email: {user['email']}</p>
        <img src="{user['avatar']}" width="60" style="border-radius: 50%;">
        
        <div class="info">
            <strong>Token value:</strong> <code>{censored_token}</code>
        </div>
        
        <a href='/logout' class='button' style='background: #ff4444;'>Logout</a>
        """
    else:
        content = """
        <p>⚠️ Not authenticated</p>
        <p>Click below to login with Speckle</p>
        <a href='/login' class='button'>Login with Speckle</a>
        """
    return render_template_string(HTML, content=content)

@app.route('/login')
def login():
    # this is the login page
    # a challenge is a random 32 digit value for safety
    # just generate a random one
    session['challenge'] = secrets.token_urlsafe(32)
    return redirect(f"{SERVER_URL}/authn/verify/{APP_ID}/{session['challenge']}")

# this is the page speckle redirects us
@app.route('/callback')
def callback():
    access_code = request.args.get('access_code')
    challenge = session.get('challenge')
    
    if not challenge:
        return "❌ Session lost. <a href='/'>Try again</a>"
    
    # request the token from server
    r = requests.post(f"{SERVER_URL}/auth/token/", json={
        "accessCode": access_code,
        "appId": APP_ID,
        "appSecret": APP_SECRET,
        "challenge": challenge
    })
    
    token = r.json()['token']
    session['token'] = token  # store token in flask session
    session.pop('challenge')
    
    # censored again
    censored = token[:4] + "•" * (len(token) - 4)
    
    content = f"""
    <p>✅ Authentication successful!</p>
    
    <div class="info">
        <strong>Token received:</strong> <code>{censored}</code><br>
    </div>
    
    <a href='/' class='button'>Continue</a>
    """
    return render_template_string(HTML, content=content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)