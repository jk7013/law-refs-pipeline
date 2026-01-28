"""
law.go.kr API 클라이언트 (ONLINE 모드용)
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from urllib.parse import urlencode


class LawGoClient:
    """law.go.kr API 클라이언트"""
    
    BASE_URL = "https://www.law.go.kr"
    CACHE_DIR = Path(".cache")
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        if cache_enabled:
            self.CACHE_DIR.mkdir(exist_ok=True)
    
    def _get_cache_path(self, law_id: str) -> Path:
        """캐시 파일 경로"""
        return self.CACHE_DIR / f"lawgo_{law_id}.json"
    
    def _load_cache(self, law_id: str) -> Optional[Dict[str, Any]]:
        """캐시에서 로드"""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(law_id)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def _save_cache(self, law_id: str, data: Dict[str, Any]):
        """캐시에 저장"""
        if not self.cache_enabled:
            return
        
        cache_path = self._get_cache_path(law_id)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get_law_info(self, law_id: str) -> Optional[Dict[str, Any]]:
        """법령 정보 조회"""
        # 캐시 확인
        cached = self._get_cache_path(law_id)
        if cached and cached.exists():
            data = self._load_cache(law_id)
            if data:
                return data
        
        # API 호출 (실제 구현은 law.go.kr API 문서 참조)
        # 여기서는 예시로만 구현
        try:
            # DRF API 엔드포인트 (실제 엔드포인트는 API 문서 확인 필요)
            url = f"{self.BASE_URL}/DRF/lawService.do"
            params = {
                "target": "law",
                "MST": law_id,
            }
            
            # 환경변수에서 토큰/키 가져오기 (하드코딩 금지)
            oc = os.getenv("LAWGO_OC")
            if oc:
                params["OC"] = oc
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 캐시 저장
            self._save_cache(law_id, data)
            
            return data
        
        except Exception as e:
            # 오류 발생 시 캐시된 데이터 반환
            cached_data = self._load_cache(law_id)
            if cached_data:
                return cached_data
            return None

