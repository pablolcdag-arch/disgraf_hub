import os
import pytest
import seo_service

def test_generate_blog_post(monkeypatch):
    class MockResponse:
        text = "```html\n<h1>Mi Producto</h1>\n<p>Desc</p>\n```"
    
    class MockModels:
        def generate_content(self, model, contents):
            return MockResponse()
            
    class MockClient:
        models = MockModels()
        
    monkeypatch.setattr(seo_service, "gemini_client", MockClient())
    
    html = seo_service.generate_blog_post("Producto Test")
    
    # Should strip ```html and ```
    assert "<h1>Mi Producto</h1>" in html
    assert "```html" not in html
    assert "```" not in html

def test_render_and_save_post(monkeypatch, tmp_path):
    monkeypatch.setattr(seo_service, "BLOG_OUTPUT_DIR", str(tmp_path))
    
    class MockTemplate:
        def render(self, post):
            return f"<html>{post['title']} - {post['content']} - {post['date']} - {post['slug']}</html>"
            
    class MockEnv:
        def __init__(self, **kwargs):
            pass
        def get_template(self, name):
            return MockTemplate()
            
    import jinja2
    monkeypatch.setattr(jinja2, "Environment", MockEnv)
    # También mockeamos seo_service.Environment para evitar problemas de import
    monkeypatch.setattr(seo_service, "Environment", MockEnv)
    
    file_path = seo_service.render_and_save_post("Test Title", "<p>Content</p>")
    
    assert file_path.endswith("test-title.html")
    assert os.path.exists(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "Test Title" in content
    assert "<p>Content</p>" in content
    assert "test-title" in content


def test_run_seo_workflow(monkeypatch, tmp_path):
    class MockResponse:
        text = "<h1>Guía de Producto</h1><p>Contenido limpio</p>"
        
    class MockModels:
        def generate_content(self, model, contents):
            return MockResponse()
            
    class MockClient:
        models = MockModels()
        
    monkeypatch.setattr(seo_service, "gemini_client", MockClient())
    monkeypatch.setattr(seo_service, "BLOG_OUTPUT_DIR", str(tmp_path))
    
    class MockTemplate:
        def render(self, post):
            return f"<html>{post['title']} - {post['content']}</html>"
            
    class MockEnv:
        def __init__(self, **kwargs):
            pass
        def get_template(self, name):
            return MockTemplate()
            
    monkeypatch.setattr(seo_service, "Environment", MockEnv)
    
    file_path = seo_service.run_seo_workflow("Producto Test")
    
    assert "guia-de-producto.html" in file_path
    assert os.path.exists(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Guía de Producto" in content
        assert "<p>Contenido limpio</p>" in content
