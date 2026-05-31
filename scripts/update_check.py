"""
Incremental update check script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github.client import GitHubClient
from src.github.exceptions import NotModifiedError
from src.parser.skill_parser import SkillParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector
from src.storage.skill_repository import SkillRepository
from src.storage.task_repository import TaskRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'update_check.log')


def run_update_check(limit: int = 100):
    """
    Run incremental update check

    Checks existing skills for updates using ETag

    Args:
        limit: Maximum number of skills to check
    """
    logger.info("="*60)
    logger.info("Starting Incremental Update Check")
    logger.info("="*60)

    task_id = None

    try:
        # Create task record
        with TaskRepository() as task_repo:
            task = task_repo.create_task(
                task_type='update_check',
                query_text=f'Checking {limit} skills'
            )
            task_id = task.id
            task_repo.start_task(task_id)

        logger.info(f"Created task ID: {task_id}")

        # Initialize components
        logger.info("Initializing components...")
        github_client = GitHubClient()
        parser = SkillParser()
        scanner = RiskScanner()
        detector = DirectoryDetector()

        # Get skills that need update check
        with SkillRepository() as skill_repo:
            skills = skill_repo.find_for_update_check(limit=limit)

        if not skills:
            logger.info("No skills found for update check")
            print("No skills found for update check")
            return

        logger.info(f"Found {len(skills)} skills to check")
        print(f"Found {len(skills)} skills to check\n")

        # Statistics
        checked_count = 0
        updated_count = 0
        not_modified_count = 0
        offline_count = 0
        failed_count = 0

        # Check each skill
        for idx, skill in enumerate(skills, 1):
            logger.info(
                f"[{idx}/{len(skills)}] Checking: "
                f"{skill.repo_full_name}/{skill.skill_path}"
            )
            print(f"[{idx}/{len(skills)}] 正在检查: {skill.name}")

            try:
                # Fetch file content with ETag
                try:
                    file_data = github_client.get_file_content(
                        skill.skill_api_url,
                        etag=skill.skill_etag
                    )
                except NotModifiedError:
                    # File not modified, just update last_checked_at
                    logger.debug(f"Not modified: {skill.skill_path}")
                    with SkillRepository() as skill_repo:
                        skill_repo.update_last_checked(skill.id)
                    not_modified_count += 1
                    checked_count += 1
                    continue

                # File was modified, re-parse and update
                content = file_data.get("content", "")
                if not content:
                    logger.warning(f"Empty content: {skill.skill_path}")
                    failed_count += 1
                    continue

                # Parse SKILL.md
                skill_meta = parser.parse(content)
                if not skill_meta:
                    logger.warning(f"Failed to parse: {skill.skill_path}")
                    failed_count += 1
                    continue

                # Get repository info
                try:
                    repo_info = github_client.get_repo_info(skill.repo_full_name)
                except Exception as e:
                    logger.warning(f"Failed to fetch repo info: {e}")
                    repo_info = {}

                # Detect directory structure
                skill_dir = skill.skill_dir
                dir_info = {"has_scripts": False, "has_assets": False, "has_references": False, "has_tests": False}

                if skill_dir:
                    try:
                        dir_items = github_client.list_directory(skill.repo_full_name, skill_dir)
                        dir_info = detector.detect(dir_items)
                    except Exception as e:
                        logger.debug(f"Failed to detect directory structure: {e}")

                # Risk scanning
                risk_level, risk_flags = scanner.scan(content, dir_info)

                # Update record
                update_data = {
                    'name': skill_meta['name'],
                    'description': skill_meta['description'],
                    'license': skill_meta['license'],
                    'compatibility': skill_meta['compatibility'],
                    'allowed_tools': skill_meta['allowed_tools'],
                    'frontmatter_json': skill_meta['frontmatter'],
                    'skill_sha': file_data.get('sha'),
                    'skill_size': file_data.get('size'),
                    'skill_etag': file_data.get('etag'),
                    'skill_last_modified': file_data.get('last_modified'),
                    'stars': repo_info.get('stars', skill.stars),
                    'forks': repo_info.get('forks', skill.forks),
                    'watchers': repo_info.get('watchers', skill.watchers),
                    'open_issues': repo_info.get('open_issues', skill.open_issues),
                    'repo_license': repo_info.get('repo_license', skill.repo_license),
                    'repo_archived': 1 if repo_info.get('archived') else 0,
                    'repo_updated_at': repo_info.get('updated_at', skill.repo_updated_at),
                    'repo_pushed_at': repo_info.get('pushed_at', skill.repo_pushed_at),
                    'has_scripts': 1 if dir_info.get('has_scripts') else 0,
                    'has_assets': 1 if dir_info.get('has_assets') else 0,
                    'has_references': 1 if dir_info.get('has_references') else 0,
                    'has_tests': 1 if dir_info.get('has_tests') else 0,
                    'risk_level': risk_level,
                    'risk_flags': risk_flags,
                    'repo_full_name': skill.repo_full_name,
                    'skill_path': skill.skill_path,
                    'repo_owner': skill.repo_owner,
                    'repo_name': skill.repo_name,
                    'repo_url': skill.repo_url,
                    'repo_default_branch': skill.repo_default_branch,
                    'skill_dir': skill.skill_dir,
                    'skill_html_url': skill.skill_html_url,
                    'skill_raw_url': skill.skill_raw_url,
                    'skill_api_url': skill.skill_api_url,
                    'source_type': skill.source_type,
                    'status': skill.status
                }

                with SkillRepository() as skill_repo:
                    skill_repo.upsert(update_data)

                logger.info(f"Updated: {skill.name}")
                updated_count += 1
                checked_count += 1

            except Exception as e:
                if "404" in str(e) or "Not Found" in str(e):
                    # Mark as offline
                    logger.warning(f"Skill offline: {skill.skill_path}")
                    with SkillRepository() as skill_repo:
                        skill_repo.mark_offline(skill.id)
                    offline_count += 1
                else:
                    logger.error(f"Failed to check {skill.skill_path}: {e}")
                    failed_count += 1

                checked_count += 1

        # Update task status
        with TaskRepository() as task_repo:
            task_repo.complete_task(
                task_id=task_id,
                total_found=checked_count,
                total_saved=updated_count,
                total_skipped=not_modified_count
            )

        # Print summary
        print("\n" + "="*60)
        print("✅ Incremental Update Check Completed")
        print("="*60)
        print(f"检查: {checked_count}")
        print(f"更新: {updated_count}")
        print(f"未修改: {not_modified_count}")
        print(f"离线: {offline_count}")
        print(f"失败: {failed_count}")
        print("="*60)

        logger.info(
            f"Update check completed: checked={checked_count}, "
            f"updated={updated_count}, not_modified={not_modified_count}, "
            f"offline={offline_count}, failed={failed_count}"
        )

    except Exception as e:
        logger.error(f"Update check failed: {e}", exc_info=True)

        # Mark task as failed
        if task_id:
            try:
                with TaskRepository() as task_repo:
                    task_repo.fail_task(task_id, str(e))
            except:
                pass

        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_update_check(limit)
