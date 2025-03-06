from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/instructors')
def instructors():
    return render_template('instructors.html')

@app.route('/marinera')
def marinera():
    return render_template('marinera.html')


if __name__ == '__main__':
    app.run(debug=True)
