import logging
import os
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class JavaCodeAnalyzerConfig(AppConfig):
    """Java Code Analyzer Application Configuration"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_agents.java_code_analyzer'
    
    def ready(self):
        """Called when application starts"""
        try:
            from django.conf import settings
            
            base_dir = getattr(settings, 'JAVA_PROJECTS_BASE_DIR', None)
            project_mapping = getattr(settings, 'PROJECT_ID_REPO_MAPPING', {})
            git_credentials = getattr(settings, 'GIT_CREDENTIALS', {})
            
            if not base_dir:
                logger.warning("JAVA_PROJECTS_BASE_DIR is not configured, skipping project initialization")
                return
                
            if not project_mapping:
                logger.info("PROJECT_ID_REPO_MAPPING is empty, no project initialization required")
                return
            
            logger.info("Checking and initializing Java projects...")
            logger.info(f"Base directory: {base_dir}")
            logger.info(f"Configured projects: {list(project_mapping.keys())}")
            
            os.makedirs(base_dir, exist_ok=True)
            
            total_projects = len(project_mapping)
            cloned_count = 0
            updated_count = 0
            error_count = 0
            
            for project_id, repo_url in project_mapping.items():
                try:
                    project_path = os.path.join(base_dir, project_id)
                    
                    if os.path.exists(project_path):
                        logger.info(f"Project {project_id} exists, checking for updates...")
                        if self._update_project(project_path, git_credentials):
                            logger.info(f"✅ Project {project_id} updated successfully")
                            updated_count += 1
                        else:
                            logger.info(f"✅ Project {project_id} is up to date")
                    else:
                        logger.info(f"Project {project_id} does not exist, cloning...")
                        if self._clone_project(repo_url, project_path, git_credentials):
                            logger.info(f"✅ Project {project_id} cloned successfully")
                            cloned_count += 1
                        else:
                            logger.error(f"❌ Project {project_id} clone failed")
                            error_count += 1
                            
                except Exception as e:
                    logger.error(f"❌ Error handling project {project_id}: {e}")
                    error_count += 1
            
            logger.info(f"Java project initialization completed:")
            logger.info(f"  Total projects: {total_projects}")
            logger.info(f"  Cloned: {cloned_count}")
            logger.info(f"  Updated: {updated_count}")
            logger.info(f"  Errors: {error_count}")
            
        except Exception as e:
            logger.error(f"Java project initialization check failed: {e}")
    
    def _clone_project(self, repo_url, project_path, git_credentials):
        """Clone repository"""
        try:
            from git import Repo
            
            auth_url = self._build_auth_url(repo_url, git_credentials)
            repo = Repo.clone_from(auth_url, project_path)
            
            if git_credentials.get('token'):
                origin = repo.remotes.origin
                origin.set_url(repo_url)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clone project {repo_url}: {e}")
            return False
    
    def _update_project(self, project_path, git_credentials):
        """Update repository"""
        try:
            from git import Repo
            
            repo = Repo(project_path)
            
            if git_credentials:
                self._configure_git_credentials(repo, git_credentials)
            
            current_commit = repo.head.commit.hexsha
            origin = repo.remotes.origin
            origin.fetch()
            
            remote_commit = origin.refs['main'].commit.hexsha if 'main' in origin.refs else origin.refs['master'].commit.hexsha
            
            if current_commit != remote_commit:
                origin.pull()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update project {project_path}: {e}")
            return False
    
    def _build_auth_url(self, repo_url, git_credentials):
        """Build URL with credentials"""
        if not git_credentials:
            return repo_url
            
        if git_credentials.get('token'):
            return repo_url.replace('http://', f'http://oauth2:{git_credentials["token"]}@').replace('https://', f'https://oauth2:{git_credentials["token"]}@')
        elif git_credentials.get('username') and git_credentials.get('password'):
            return repo_url.replace('http://', f'http://{git_credentials["username"]}:{git_credentials["password"]}@').replace('https://', f'https://{git_credentials["username"]}:{git_credentials["password"]}@')
        
        return repo_url
    
    def _configure_git_credentials(self, repo, git_credentials):
        """Configure Git credentials"""
        try:
            with repo.config_writer() as config:
                if git_credentials.get('token'):
                    config.set_value('user', 'name', 'GitLab CI')
                    config.set_value('user', 'email', 'ci@example.com')
                elif git_credentials.get('username'):
                    config.set_value('user', 'name', git_credentials['username'])
                    config.set_value('user', 'email', f'{git_credentials["username"]}@example.com')
        except Exception as e:
            logger.warning(f"Failed to configure Git credentials: {e}")