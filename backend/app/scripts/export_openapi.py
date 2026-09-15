"""Regenerate the API schema from the running application's route definitions."""
from pathlib import Path
import yaml
from app.main import app

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[3] / 'docs' / 'api' / 'openapi.yaml'
    target.write_text(yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True), encoding='utf-8')
