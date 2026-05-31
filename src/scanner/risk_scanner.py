"""
Risk scanner for SKILL.md content
"""
from typing import List, Tuple, Dict
from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RiskScanner:
    """
    Scanner for detecting security risks in SKILL.md content

    Risk levels:
    - low: Only SKILL.md, no scripts, no dangerous keywords
    - medium: Contains scripts, needs API key, needs network access
    - high: Contains dangerous commands, secrets, private keys
    """

    def __init__(self):
        """Initialize risk scanner with keyword lists"""
        self.high_risk_keywords = Config.HIGH_RISK_KEYWORDS
        self.medium_risk_keywords = Config.MEDIUM_RISK_KEYWORDS

    def scan(self, content: str, dir_info: Dict[str, bool]) -> Tuple[str, List[str]]:
        """
        Scan content and directory info for security risks

        Args:
            content: SKILL.md content
            dir_info: Directory structure info (has_scripts, has_assets, etc.)

        Returns:
            Tuple of (risk_level, risk_flags)
        """
        if not content:
            return "unknown", []

        flags = []
        lower_content = content.lower()

        # Scan for high-risk keywords
        for keyword in self.high_risk_keywords:
            if keyword.lower() in lower_content:
                flag_name = self._keyword_to_flag(keyword)
                flags.append(flag_name)
                logger.warning(f"High-risk keyword detected: {keyword}")

        # Scan for medium-risk keywords
        for keyword in self.medium_risk_keywords:
            if keyword.lower() in lower_content:
                flag_name = self._keyword_to_flag(keyword)
                flags.append(flag_name)
                logger.debug(f"Medium-risk keyword detected: {keyword}")

        # Check directory structure
        if dir_info.get("has_scripts"):
            flags.append("contains_scripts")

        # Additional pattern checks
        if "api key" in lower_content or "apikey" in lower_content:
            flags.append("needs_api_key")

        if "http://" in lower_content or "https://" in lower_content:
            flags.append("needs_network")

        # Determine risk level
        risk_level = self._calculate_risk_level(flags)

        # Remove duplicates and sort
        flags = sorted(set(flags))

        logger.info(f"Risk scan complete: level={risk_level}, flags={len(flags)}")
        return risk_level, flags

    def _keyword_to_flag(self, keyword: str) -> str:
        """
        Convert keyword to flag name

        Args:
            keyword: Risk keyword

        Returns:
            Flag name
        """
        # Map keywords to flag names
        keyword_map = {
            "rm -rf": "dangerous_delete",
            "curl | bash": "remote_shell",
            "wget": "network_download",
            "eval(": "dynamic_eval",
            "exec(": "dynamic_exec",
            "subprocess": "command_execute",
            "os.system": "command_execute",
            "process.env": "env_access",
            ".env": "env_file_access",
            "API_KEY": "api_key",
            "SECRET": "secret",
            "TOKEN": "token",
            "PRIVATE_KEY": "private_key",
            "id_rsa": "ssh_key",
            "ssh": "ssh_access"
        }

        return keyword_map.get(keyword, keyword.lower().replace(" ", "_").replace("(", ""))

    def _calculate_risk_level(self, flags: List[str]) -> str:
        """
        Calculate overall risk level based on flags

        Args:
            flags: List of risk flags

        Returns:
            Risk level: low/medium/high
        """
        # High-risk flags
        high_flags = {
            "dangerous_delete",
            "remote_shell",
            "env_file_access",
            "private_key",
            "ssh_key"
        }

        # Check for high-risk flags
        if any(flag in high_flags for flag in flags):
            return "high"

        # Check for any flags (medium risk)
        if flags:
            return "medium"

        # No flags (low risk)
        return "low"

    def get_risk_description(self, risk_level: str) -> str:
        """
        Get human-readable risk description

        Args:
            risk_level: Risk level

        Returns:
            Risk description
        """
        descriptions = {
            "low": "仅包含 SKILL.md，无脚本，无危险命令",
            "medium": "包含脚本或需要 API Key、网络访问",
            "high": "包含危险命令、密钥或敏感信息",
            "unknown": "未知风险"
        }

        return descriptions.get(risk_level, "未知风险")
