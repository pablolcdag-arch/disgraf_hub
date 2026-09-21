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

def test_post_to_wordpress(monkeypatch):
    monkeypatch.setattr(seo_service, "WP_URL", "http://test.com")
    monkeypatch.setattr(seo_service, "WP_USER", "user")
    monkeypatch.setattr(seo_service, "WP_APP_PASSWORD", "pass")
    
    class MockPostResponse:
        status_code = 201
        text = ""
        def json(self):
            return {"link": "http://test.com/post/1"}
            
    def mock_post(*args, **kwargs):
        assert kwargs["json"]["title"] == "Test Title"
        assert kwargs["json"]["content"] == "<p>Content</p>"
        return MockPostResponse()
        
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    
    link = seo_service.post_to_wordpress("Test Title", "<p>Content</p>")
    assert link == "http://test.com/post/1"

def test_run_seo_workflow(monkeypatch):
    class MockResponse:
        text = "<h1>Guía de Producto</h1><p>Contenido limpio</p>"
        
    class MockModels:
        def generate_content(self, model, contents):
            return MockResponse()
            
    class MockClient:
        models = MockModels()
        
    monkeypatch.setattr(seo_service, "gemini_client", MockClient())
    
    monkeypatch.setattr(seo_service, "WP_URL", "http://test.com")
    monkeypatch.setattr(seo_service, "WP_USER", "user")
    monkeypatch.setattr(seo_service, "WP_APP_PASSWORD", "pass")
    
    class MockPostResponse:
        status_code = 201
        def json(self):
            return {"link": "http://test.com/post/2"}
            
    def mock_post(*args, **kwargs):
        assert kwargs["json"]["title"] == "Guía de Producto"
        assert kwargs["json"]["content"] == "<p>Contenido limpio</p>"
        return MockPostResponse()
        
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    
    link = seo_service.run_seo_workflow("Producto Test")
    assert link == "http://test.com/post/2"

