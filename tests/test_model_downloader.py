import os
from unittest.mock import patch
from naturalization_layer.model_downloader import download_model

def test_download_model(tmp_path):
    dest_path = os.path.join(tmp_path, "test_dir", "test_model.gguf")
    
    # Verify file doesn't exist yet
    assert not os.path.exists(dest_path)
    
    # Mock urllib.request.urlretrieve so we don't download a 3.2GB file in tests
    with patch("urllib.request.urlretrieve") as mock_retrieve, \
         patch("naturalization_layer.model_downloader.EXPECTED_SIZE", 19):
        # Create a dummy file when urlretrieve is called to simulate successful download
        def side_effect(url, filename=None, reporthook=None, *args, **kwargs):
            if reporthook:
                reporthook(1, 1024, 1024)
            with open(filename, "w") as f:
                f.write("dummy model content")
        
        mock_retrieve.side_effect = side_effect
        
        download_model(dest_path)
        
        assert mock_retrieve.call_count == 1
        assert os.path.exists(dest_path)
        
        # Calling download_model again should skip since the file exists now
        mock_retrieve.reset_mock()
        download_model(dest_path)
        assert mock_retrieve.call_count == 0
