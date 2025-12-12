"""
Profile 管理器
管理 LIS Profile 的创建、加载、保存、删除
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .logger import get_logger

logger = get_logger(__name__)


class ProfileManager:
    """
    LIS Profile 配置文件管理器
    """
    
    def __init__(self, profiles_dir: str = "profiles/lis_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def list_profiles(self) -> List[Dict]:
        """
        列出所有 profile
        返回: [{id, name, description, file_path, created_time}, ...]
        """
        profiles = []
        
        for file_path in self.profiles_dir.glob("*.yaml"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                profiles.append({
                    'id': data.get('id', ''),
                    'name': file_path.stem,
                    'description': data.get('description', ''),
                    'file_path': str(file_path),
                    'created_time': datetime.fromtimestamp(file_path.stat().st_ctime)
                })
            except Exception as e:
                logger.warning(f"读取 profile 失败 {file_path}: {e}")
        
        # 按创建时间排序
        profiles.sort(key=lambda x: x['created_time'], reverse=True)
        
        return profiles
    
    def load_profile(self, profile_id: str) -> Optional[Dict]:
        """加载指定的 profile"""
        file_path = self.profiles_dir / f"{profile_id}.yaml"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载 profile 失败: {e}")
            return None
    
    def save_profile(self, profile: Dict) -> str:
        """
        保存 profile
        返回保存的文件路径
        """
        profile_id = profile.get('id', 'unnamed_profile')
        
        # 清理文件名中的特殊字符
        safe_id = "".join(c for c in profile_id if c.isalnum() or c in ('_', '-'))
        
        file_path = self.profiles_dir / f"{safe_id}.yaml"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return str(file_path)
    
    def delete_profile(self, profile_id: str) -> bool:
        """删除指定的 profile"""
        file_path = self.profiles_dir / f"{profile_id}.yaml"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def profile_exists(self, profile_id: str) -> bool:
        """检查 profile 是否存在"""
        file_path = self.profiles_dir / f"{profile_id}.yaml"
        return file_path.exists()
    
    def create_profile_from_wizard(self, 
                                   profile_id: str,
                                   description: str,
                                   column_mapping: Dict,
                                   test_mapping: Dict,
                                   value_parsing: Dict,
                                   required_columns: List[str],
                                   skip_top_rows: int = 0,
                                   output_options: Optional[Dict] = None) -> Dict:
        """
        从向导数据创建 profile
        """
        profile = {
            'id': profile_id,
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'signature': {
                'required_columns': required_columns,
                'min_match_ratio': 0.75,
                'skip_top_rows': skip_top_rows
            },
            'column_mapping': column_mapping,
            'test_mapping': test_mapping,
            'value_parsing': value_parsing,
            'output_options': output_options or {
                'drop_unknown_tests': True,
                'drop_failed_rows': False
            }
        }
        
        return profile

