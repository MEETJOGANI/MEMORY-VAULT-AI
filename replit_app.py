import streamlit.web.bootstrap as bootstrap
from streamlit import config

# Force the port to be 5000 and host to be 0.0.0.0
config.set_option("server.port", 5000)
config.set_option("server.address", "0.0.0.0")
config.set_option("server.headless", True)
config.set_option("server.enableCORS", False)
config.set_option("server.enableXsrfProtection", False)
config.set_option("browser.gatherUsageStats", False)

# Run the app
bootstrap.run("app.py", "", [], flag_options={})