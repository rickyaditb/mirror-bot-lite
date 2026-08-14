export PYTHONUNBUFFERED=1
if [ -d "mltbenv" ]; then
    source mltbenv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi
python3 -u update.py
python3 -u -m bot
