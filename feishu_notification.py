import logging
import requests
from typing import Dict, Any
from datetime import datetime
from config import LARK_CONFIG

logger = logging.getLogger(__name__)


class FeishuNotifier:
    """lark机器人通知器。"""
    
    def __init__(self, webhook_url: str):
        """
        初始化lark通知器。
        
        参数:
            webhook_url: lark机器人 webhook URL
        """
        self.webhook_url = webhook_url
        
    def send_jacoco_report(
        self,
        repo_url: str,
        branch_name: str,
        commit_id: str,
        coverage_data: Dict[str, Any],
        scan_result: Dict[str, Any],
        request_id: str,
        html_report_url: str = None
    ) -> bool:
        """
        发送 JaCoCo 覆盖率报告到lark。
        
        参数:
            repo_url: 仓库 URL
            branch_name: 分支名称
            commit_id: 提交 ID
            coverage_data: 覆盖率数据
            scan_result: 扫描结果
            request_id: 请求 ID
            
        返回:
            是否发送成功
        """
        try:
            # 构建消息内容
            message = self._build_jacoco_message(
                repo_url, branch_name, commit_id, coverage_data, scan_result, request_id, html_report_url
            )
            
            # 发送消息
            return self._send_message(message)
            
        except Exception as e:
            logger.error(f"[{request_id}] 发送lark通知失败: {str(e)}")
            return False
    
    def send_error_notification(
        self,
        repo_url: str,
        branch_name: str,
        commit_id: str,
        error_message: str,
        request_id: str
    ) -> bool:
        """
        发送错误通知到lark。
        
        参数:
            repo_url: 仓库 URL
            branch_name: 分支名称
            commit_id: 提交 ID
            error_message: 错误消息
            request_id: 请求 ID
            
        返回:
            是否发送成功
        """
        try:
            # 构建错误消息
            message = self._build_error_message(
                repo_url, branch_name, commit_id, error_message, request_id
            )
            
            # 发送消息
            return self._send_message(message)
            
        except Exception as e:
            logger.error(f"[{request_id}] 发送lark错误通知失败: {str(e)}")
            return False
    
    def _build_jacoco_message(
        self,
        repo_url: str,
        branch_name: str,
        commit_id: str,
        coverage_data: Dict[str, Any],
        scan_result: Dict[str, Any],
        request_id: str,
        html_report_url: str = None
    ) -> Dict[str, Any]:
        """构建 JaCoCo 报告消息。"""
        
        # 提取覆盖率数据
        instruction_coverage = coverage_data.get('instruction_coverage', 0)
        branch_coverage = coverage_data.get('branch_coverage', 0)
        line_coverage = coverage_data.get('line_coverage', 0)
        complexity_coverage = coverage_data.get('complexity_coverage', 0)
        method_coverage = coverage_data.get('method_coverage', 0)
        class_coverage = coverage_data.get('class_coverage', 0)
        
        # 确定覆盖率等级和颜色
        avg_coverage = (line_coverage + branch_coverage) / 2
        if avg_coverage >= 80:
            coverage_level = "优秀"
            color = "green"
        elif avg_coverage >= 60:
            coverage_level = "良好"
            color = "yellow"
        else:
            coverage_level = "需改进"
            color = "red"
        
        # 获取仓库名称
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        # 构建富文本消息
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 JaCoCo 覆盖率报告 - {repo_name}"
                    },
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**仓库**: {repo_name}\n**分支**: {branch_name}\n**提交**: `{commit_id[:8]}`\n**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"## 📈 覆盖率统计\n\n**整体评级**: {coverage_level}\n\n**详细数据**:\n- ⚡ **指令覆盖率**: {instruction_coverage:.1f}%\n- 🌿 **分支覆盖率**: {branch_coverage:.1f}%\n- 🎯 **行覆盖率**: {line_coverage:.1f}%\n- 🔄 **圈复杂度覆盖率**: {complexity_coverage:.1f}%\n- 🔧 **方法覆盖率**: {method_coverage:.1f}%\n- 📦 **类覆盖率**: {class_coverage:.1f}%"
                        }
                    }
                ]
            }
        }
        
        # 添加HTML报告链接按钮（如果有）
        if html_report_url:
            message["card"]["elements"].append({
                "tag": "hr"
            })
            message["card"]["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📊 查看详细报告"
                        },
                        "type": "primary",
                        "url": html_report_url
                    }
                ]
            })

        # 添加报告文件信息（如果有）
        elif scan_result.get('reports_dir'):
            message["card"]["elements"].append({
                "tag": "hr"
            })
            message["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📋 **报告文件**: 已生成在 `{scan_result['reports_dir']}`"
                }
            })
        
        # 添加请求ID
        message["card"]["elements"].append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"请求ID: {request_id}"
                }
            ]
        })
        
        return message
    
    def _build_error_message(
        self,
        repo_url: str,
        branch_name: str,
        commit_id: str,
        error_message: str,
        request_id: str
    ) -> Dict[str, Any]:
        """构建错误通知消息。"""
        
        # 获取仓库名称
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"❌ JaCoCo 扫描失败 - {repo_name}"
                    },
                    "template": "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**仓库**: {repo_name}\n**分支**: {branch_name}\n**提交**: `{commit_id[:8]}`\n**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"## ⚠️ 错误信息\n\n```\n{error_message}\n```"
                        }
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"请求ID: {request_id}"
                            }
                        ]
                    }
                ]
            }
        }
        
        return message
    
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到lark。"""

        # 检查是否启用通知
        if not LARK_CONFIG.get("enable_notifications", True):
            logger.info("Lark通知已禁用，跳过发送")
            return True

        retry_count = LARK_CONFIG.get("retry_count", 3)
        retry_delay = LARK_CONFIG.get("retry_delay", 1)
        timeout = LARK_CONFIG.get("timeout", 10)

        for attempt in range(retry_count):
            try:
                headers = {
                    'Content-Type': 'application/json'
                }

                response = requests.post(
                    self.webhook_url,
                    headers=headers,
                    json=message,
                    timeout=timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        logger.info("lark通知发送成功")
                        return True
                    else:
                        logger.error(f"lark通知发送失败: {result}")
                        if attempt < retry_count - 1:
                            logger.info(f"第{attempt + 1}次重试...")
                            import time
                            time.sleep(retry_delay)
                            continue
                        return False
                else:
                    logger.error(f"lark通知发送失败，状态码: {response.status_code}")
                    if attempt < retry_count - 1:
                        logger.info(f"第{attempt + 1}次重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    return False

            except Exception as e:
                logger.error(f"发送lark通知异常: {str(e)}")
                if attempt < retry_count - 1:
                    logger.info(f"第{attempt + 1}次重试...")
                    import time
                    time.sleep(retry_delay)
                    continue
                return False

        return False


def send_jacoco_notification(
    webhook_url: str,
    repo_url: str,
    branch_name: str,
    commit_id: str,
    coverage_data: Dict[str, Any],
    scan_result: Dict[str, Any],
    request_id: str,
    html_report_url: str = None
) -> bool:
    """
    发送 JaCoCo 覆盖率通知的便捷函数。
    
    参数:
        webhook_url: lark机器人 webhook URL
        repo_url: 仓库 URL
        branch_name: 分支名称
        commit_id: 提交 ID
        coverage_data: 覆盖率数据
        scan_result: 扫描结果
        request_id: 请求 ID
        
    返回:
        是否发送成功
    """
    if not webhook_url:
        logger.warning(f"[{request_id}] 未配置lark webhook URL，跳过通知")
        return False
    
    notifier = FeishuNotifier(webhook_url)
    return notifier.send_jacoco_report(
        repo_url, branch_name, commit_id, coverage_data, scan_result, request_id, html_report_url
    )


def send_error_notification(
    webhook_url: str,
    repo_url: str,
    branch_name: str,
    commit_id: str,
    error_message: str,
    request_id: str
) -> bool:
    """
    发送错误通知的便捷函数。
    
    参数:
        webhook_url: lark机器人 webhook URL
        repo_url: 仓库 URL
        branch_name: 分支名称
        commit_id: 提交 ID
        error_message: 错误消息
        request_id: 请求 ID
        
    返回:
        是否发送成功
    """
    if not webhook_url:
        logger.warning(f"[{request_id}] 未配置lark webhook URL，跳过错误通知")
        return False
    
    notifier = FeishuNotifier(webhook_url)
    return notifier.send_error_notification(
        repo_url, branch_name, commit_id, error_message, request_id
    )
