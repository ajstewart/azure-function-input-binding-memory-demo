import azure.functions as func

from memory_test_func import memory_bp

app = func.FunctionApp()

app.register_blueprint(memory_bp)
