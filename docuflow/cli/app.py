"""
CLI 入口点

使用 Typer 提供命令行界面。
"""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from docuflow.core.config import create_app_config, get_available_models, get_settings
from docuflow.core.orchestrator import WorkflowOrchestrator
from docuflow.utils import setup_logging

app = typer.Typer(
    name="docuflow",
    help="DocuFlow-AI: 将需求文档转换为结构化设计文档",
    add_completion=False
)

console = Console()


def get_orchestrator(
    project_root: Path,
    project_name: str = "default",
    model_name: Optional[str] = None
) -> WorkflowOrchestrator:
    """创建调度器"""
    config = create_app_config(project_root, project_name, model_name)
    return WorkflowOrchestrator(config)


# 公共参数
def common_options(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志")
):
    return project_root, project_name, model_name, verbose


@app.command()
def init(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志")
):
    """阶段 1：初始化项目 - 生成术语表和 DAG"""
    setup_logging(level=10 if verbose else 20)
    model = model_name or get_settings().model_name

    console.print(Panel.fit(
        f"[bold blue]DocuFlow-AI 初始化[/bold blue]\n"
        f"项目: [cyan]{project_name}[/cyan]\n"
        f"模型: [cyan]{model}[/cyan]",
        border_style="blue"
    ))

    orchestrator = get_orchestrator(project_root, project_name, model_name)

    console.print(f"\n输入目录: {orchestrator.config.input_dir}")
    console.print(f"工作目录: {orchestrator.config.workspace_dir}")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("正在初始化...", total=None)
        success = orchestrator.run_init()

    if success:
        console.print("\n[green]初始化成功！[/green]")
        console.print(f"  - {orchestrator.config.glossary_file}")
        console.print(f"  - {orchestrator.config.dag_file}")
        console.print(f"\n[yellow]下一步:[/yellow] python -m docuflow run -p {project_name} -m {model}")
    else:
        console.print("\n[red]初始化失败！[/red]")
        raise typer.Exit(1)


@app.command()
def run(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    step: bool = typer.Option(False, "--step", "-s", help="逐步模式"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志")
):
    """阶段 2：运行拓扑生成 - 按依赖顺序生成模块设计"""
    setup_logging(level=10 if verbose else 20)
    model = model_name or get_settings().model_name

    console.print(Panel.fit(
        f"[bold blue]DocuFlow-AI 生成[/bold blue]\n"
        f"项目: [cyan]{project_name}[/cyan]\n"
        f"模型: [cyan]{model}[/cyan]\n"
        f"模式: {'逐步' if step else '连续'}",
        border_style="blue"
    ))

    orchestrator = get_orchestrator(project_root, project_name, model_name)

    try:
        status_info = orchestrator.display_status()
        console.print(f"\n进度: {status_info['progress']['completed']}/{status_info['progress']['total']} 完成")
    except FileNotFoundError:
        console.print("[red]错误: 请先运行 'init'[/red]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("正在生成模块设计...", total=None)
        success = orchestrator.run_generation(step_by_step=step)

    if success:
        status_info = orchestrator.display_status()
        console.print(f"\n[green]进度: {status_info['progress']['percentage']}[/green]")
        if status_info['progress']['pending'] == 0:
            console.print(f"\n[yellow]下一步:[/yellow] python -m docuflow overview -p {project_name} -m {model}")
    else:
        console.print("\n[red]生成失败！[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
):
    """查看当前项目进度"""
    model = model_name or get_settings().model_name
    orchestrator = get_orchestrator(project_root, project_name, model_name)

    try:
        status_info = orchestrator.display_status()
    except FileNotFoundError:
        console.print("[red]错误: 请先运行 'init'[/red]")
        raise typer.Exit(1)

    console.print(Panel.fit(
        f"[bold]{status_info['project_name']}[/bold]\n"
        f"项目: [cyan]{project_name}[/cyan]\n"
        f"模型: [cyan]{model}[/cyan]\n"
        f"阶段: {status_info['current_phase']}\n"
        f"最后运行: {status_info['last_run']}",
        title="项目状态", border_style="blue"
    ))

    prog = status_info['progress']
    console.print(f"\n[bold]进度:[/bold] {prog['completed']}/{prog['total']} ({prog['percentage']})")

    if status_info['modules']:
        table = Table(title="\n模块状态")
        table.add_column("模块", style="cyan")
        table.add_column("状态")
        table.add_column("文件", style="dim")

        status_colors = {"completed": "green", "pending": "yellow", "processing": "blue", "failed": "red"}
        status_labels = {"completed": "已完成", "pending": "待处理", "processing": "处理中", "failed": "失败"}

        for module in status_info['modules']:
            color = status_colors.get(module['status'], "white")
            label = status_labels.get(module['status'], module['status'])
            table.add_row(module['name'], f"[{color}]{label}[/{color}]", module['file_path'] or "-")

        console.print(table)


@app.command()
def overview(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志")
):
    """阶段 3：生成系统概述"""
    setup_logging(level=10 if verbose else 20)
    model = model_name or get_settings().model_name

    console.print(Panel.fit(
        f"[bold blue]DocuFlow-AI 系统概述[/bold blue]\n"
        f"项目: [cyan]{project_name}[/cyan]\n"
        f"模型: [cyan]{model}[/cyan]",
        border_style="blue"
    ))

    orchestrator = get_orchestrator(project_root, project_name, model_name)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("正在生成系统概述...", total=None)
        success = orchestrator.run_overview()

    if success:
        console.print("\n[green]系统概述生成成功！[/green]")
        console.print(f"\n[yellow]下一步:[/yellow] python -m docuflow assemble -p {project_name} -m {model}")
    else:
        console.print("\n[red]系统概述生成失败！[/red]")
        raise typer.Exit(1)


@app.command()
def assemble(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志")
):
    """阶段 4：组装最终文档"""
    setup_logging(level=10 if verbose else 20)
    model = model_name or get_settings().model_name

    console.print(Panel.fit(
        f"[bold blue]DocuFlow-AI 组装[/bold blue]\n"
        f"项目: [cyan]{project_name}[/cyan]\n"
        f"模型: [cyan]{model}[/cyan]",
        border_style="blue"
    ))

    orchestrator = get_orchestrator(project_root, project_name, model_name)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("正在组装最终文档...", total=None)
        success = orchestrator.run_assembly()

    if success:
        output_file = orchestrator.config.output_dir / "final_design_document.md"
        console.print(f"\n[green]文档组装成功！[/green]\n输出: {output_file}")
    else:
        console.print("\n[red]组装失败！[/red]")
        raise typer.Exit(1)


@app.command()
def reset(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    module: Optional[str] = typer.Option(None, "--module", help="重置指定模块"),
    all_modules: bool = typer.Option(False, "--all", help="重置所有模块")
):
    """重置模块状态"""
    from docuflow.core.models import ProjectStatus, ModuleStatus
    from docuflow.utils import safe_read_yaml, safe_write_yaml

    config = create_app_config(project_root, project_name, model_name)
    status = safe_read_yaml(config.status_file, ProjectStatus)

    if status is None:
        console.print("[red]错误: 未找到状态文件[/red]")
        raise typer.Exit(1)

    if all_modules:
        for m in status.modules:
            m.status = ModuleStatus.PENDING
            m.error_message = None
        console.print("[yellow]所有模块已重置[/yellow]")
    elif module:
        found = False
        for m in status.modules:
            if m.name == module:
                m.status = ModuleStatus.PENDING
                m.error_message = None
                found = True
                console.print(f"[yellow]模块 '{module}' 已重置[/yellow]")
                break
        if not found:
            console.print(f"[red]未找到模块 '{module}'[/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]请指定 --module 或 --all[/red]")
        raise typer.Exit(1)

    safe_write_yaml(config.status_file, status)


@app.command()
def all(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
    project_name: str = typer.Option("default", "--project", "-p", help="项目名称"),
    model_name: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    step: bool = typer.Option(False, "--step", "-s", help="逐步模式（每个模块后暂停）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志")
):
    """一键运行完整流程：init -> run -> overview -> assemble"""
    setup_logging(level=10 if verbose else 20)
    model = model_name or get_settings().model_name

    console.print(Panel.fit(
        f"[bold blue]DocuFlow-AI 完整流程[/bold blue]\n"
        f"项目: [cyan]{project_name}[/cyan]\n"
        f"模型: [cyan]{model}[/cyan]",
        border_style="blue"
    ))

    orchestrator = get_orchestrator(project_root, project_name, model_name)

    console.print(f"\n输入目录: {orchestrator.config.input_dir}")
    console.print(f"输出目录: {orchestrator.config.output_dir}\n")

    # 阶段 1: 初始化
    console.print("[bold]━━━ 阶段 1/4: 初始化 ━━━[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("生成术语表和 DAG...", total=None)
        success = orchestrator.run_init()

    if not success:
        console.print("\n[red]初始化失败！[/red]")
        raise typer.Exit(1)
    console.print("[green]✓ 初始化完成[/green]\n")

    # 阶段 2: 模块生成
    console.print("[bold]━━━ 阶段 2/4: 模块设计生成 ━━━[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("按拓扑顺序生成模块设计...", total=None)
        success = orchestrator.run_generation(step_by_step=step)

    if not success:
        console.print("\n[red]模块生成失败！[/red]")
        raise typer.Exit(1)

    # 如果是逐步模式且还有待处理模块，提示用户继续
    status_info = orchestrator.display_status()
    if step and status_info['progress']['pending'] > 0:
        console.print(f"[yellow]逐步模式：还有 {status_info['progress']['pending']} 个模块待处理[/yellow]")
        console.print(f"继续运行: python -m docuflow run -p {project_name} -m {model}")
        return

    console.print("[green]✓ 模块设计完成[/green]\n")

    # 阶段 3: 系统概述
    console.print("[bold]━━━ 阶段 3/4: 系统概述生成 ━━━[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("生成系统设计、接口设计、数据库设计...", total=None)
        success = orchestrator.run_overview()

    if not success:
        console.print("\n[red]系统概述生成失败！[/red]")
        raise typer.Exit(1)
    console.print("[green]✓ 系统概述完成[/green]\n")

    # 阶段 4: 组装
    console.print("[bold]━━━ 阶段 4/4: 文档组装 ━━━[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("组装最终设计文档...", total=None)
        success = orchestrator.run_assembly()

    if not success:
        console.print("\n[red]文档组装失败！[/red]")
        raise typer.Exit(1)

    output_file = orchestrator.config.output_dir / "final_design_document.md"
    console.print("[green]✓ 文档组装完成[/green]\n")

    # 完成
    console.print(Panel.fit(
        f"[bold green]全部完成！[/bold green]\n\n"
        f"输出文件: [cyan]{output_file}[/cyan]",
        border_style="green"
    ))


@app.command()
def models():
    """列出所有可用模型"""
    available = get_available_models()
    default_model = get_settings().model_name

    console.print(Panel.fit("[bold]可用模型[/bold]", border_style="blue"))

    table = Table()
    table.add_column("模型", style="cyan")
    table.add_column("状态")

    for model in available:
        status = "[green]默认[/green]" if model == default_model else ""
        table.add_row(model, status)

    console.print(table)
    console.print(f"\n使用 [cyan]--model[/cyan] 或 [cyan]-m[/cyan] 指定模型")
    console.print(f"或设置环境变量 [cyan]DOCUFLOW_MODEL_NAME[/cyan]")


@app.command()
def list_projects(
    project_root: Path = typer.Option(Path("."), "--root", "-r", help="项目根目录"),
):
    """列出所有项目"""
    data_dir = project_root / "data"
    input_dir = data_dir / "input"

    if not input_dir.exists():
        console.print("[yellow]未找到任何项目[/yellow]")
        return

    console.print(Panel.fit("[bold]项目列表[/bold]", border_style="blue"))

    table = Table()
    table.add_column("项目", style="cyan")
    table.add_column("模型输出")

    for project_dir in input_dir.iterdir():
        if project_dir.is_dir():
            project_name = project_dir.name
            # 查找该项目下的模型输出
            model_outputs = []
            project_output_dir = data_dir / project_name
            if project_output_dir.exists():
                for model_dir in project_output_dir.iterdir():
                    if model_dir.is_dir():
                        model_outputs.append(model_dir.name)

            table.add_row(project_name, ", ".join(model_outputs) or "-")

    console.print(table)


def main():
    """主入口点"""
    app()


if __name__ == "__main__":
    main()
