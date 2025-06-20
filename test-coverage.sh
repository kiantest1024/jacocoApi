#!/bin/bash

# JaCoCo 覆盖率测试脚本
set -e

echo "🧪 JaCoCo 覆盖率测试工具"
echo "========================"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}💡 $1${NC}"; }

# 测试参数
REPO_URL="http://172.16.1.30/kian/jacocotest.git"
COMMIT_ID="main"
BRANCH="main"
SERVICE_NAME="jacocotest"

# 创建测试报告目录
TEST_REPORTS_DIR="test_reports_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_REPORTS_DIR"

print_info "测试报告目录: $TEST_REPORTS_DIR"

# 测试1: Docker扫描测试
test_docker_scan() {
    echo ""
    echo "🐳 测试 Docker 扫描..."
    
    if ! docker images | grep -q "jacoco-scanner.*latest"; then
        print_error "jacoco-scanner 镜像不存在"
        print_info "请先运行: ./rebuild-scanner.sh"
        return 1
    fi
    
    local docker_reports="$TEST_REPORTS_DIR/docker"
    mkdir -p "$docker_reports"
    
    print_info "运行 Docker 扫描..."
    if timeout 300 docker run --rm \
        -v "$(pwd)/$docker_reports:/app/reports" \
        jacoco-scanner:latest \
        --repo-url "$REPO_URL" \
        --commit-id "$COMMIT_ID" \
        --branch "$BRANCH" \
        --service-name "$SERVICE_NAME"; then
        
        print_success "Docker 扫描完成"
        
        # 分析结果
        analyze_results "$docker_reports" "Docker"
        
    else
        print_error "Docker 扫描失败或超时"
        return 1
    fi
}

# 测试2: 本地扫描测试
test_local_scan() {
    echo ""
    echo "🏠 测试本地扫描..."
    
    if ! command -v mvn &> /dev/null; then
        print_warning "Maven 未安装，跳过本地扫描测试"
        return 0
    fi
    
    local local_reports="$TEST_REPORTS_DIR/local"
    mkdir -p "$local_reports"
    
    # 克隆项目到临时目录
    local temp_project="$TEST_REPORTS_DIR/temp_project"
    
    print_info "克隆测试项目..."
    if git clone "$REPO_URL" "$temp_project"; then
        cd "$temp_project"
        
        print_info "运行本地 Maven 测试..."
        if mvn clean test jacoco:report -Dmaven.test.failure.ignore=true; then
            print_success "本地扫描完成"
            
            # 复制报告
            if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
                cp "target/site/jacoco/jacoco.xml" "$local_reports/"
                cp -r "target/site/jacoco" "$local_reports/html" 2>/dev/null || true
            fi
            
            cd "$SCRIPT_DIR"
            analyze_results "$local_reports" "本地"
        else
            print_warning "本地扫描失败"
            cd "$SCRIPT_DIR"
        fi
    else
        print_error "项目克隆失败"
    fi
}

# 测试3: API扫描测试
test_api_scan() {
    echo ""
    echo "🌐 测试 API 扫描..."
    
    # 检查API是否运行
    if ! curl -s http://localhost:8002/health > /dev/null; then
        print_warning "JaCoCo API 未运行，跳过API测试"
        print_info "启动API: python3 app.py"
        return 0
    fi
    
    print_info "发送API扫描请求..."
    
    local api_response=$(curl -s -X POST http://localhost:8002/github/webhook-no-auth \
        -H "Content-Type: application/json" \
        -d "{
            \"object_kind\": \"push\",
            \"project\": {
                \"name\": \"$SERVICE_NAME\",
                \"http_url\": \"$REPO_URL\"
            },
            \"commits\": [{\"id\": \"$COMMIT_ID\"}],
            \"ref\": \"refs/heads/$BRANCH\"
        }")
    
    if echo "$api_response" | grep -q "completed"; then
        print_success "API 扫描请求成功"
        
        # 检查生成的报告
        if [[ -d "reports/$SERVICE_NAME" ]]; then
            local latest_report=$(ls -t reports/$SERVICE_NAME/ | head -1)
            if [[ -n "$latest_report" ]]; then
                print_info "最新报告: reports/$SERVICE_NAME/$latest_report"
                
                # 复制到测试目录
                local api_reports="$TEST_REPORTS_DIR/api"
                mkdir -p "$api_reports"
                cp -r "reports/$SERVICE_NAME/$latest_report"/* "$api_reports/" 2>/dev/null || true
                
                analyze_results "$api_reports" "API"
            fi
        fi
    else
        print_error "API 扫描失败"
        print_info "响应: $api_response"
    fi
}

# 分析扫描结果
analyze_results() {
    local reports_dir="$1"
    local scan_type="$2"
    
    echo ""
    echo "📊 分析 $scan_type 扫描结果..."
    
    if [[ ! -f "$reports_dir/jacoco.xml" ]]; then
        print_error "$scan_type 扫描未生成 jacoco.xml"
        return 1
    fi
    
    print_success "找到 jacoco.xml 报告"
    
    # 检查文件大小
    local file_size=$(stat -f%z "$reports_dir/jacoco.xml" 2>/dev/null || stat -c%s "$reports_dir/jacoco.xml" 2>/dev/null || echo "0")
    print_info "报告文件大小: $file_size bytes"
    
    if [[ $file_size -lt 100 ]]; then
        print_warning "报告文件太小，可能是空报告"
    fi
    
    # 解析覆盖率
    if command -v python3 &> /dev/null && [[ -f "docker/scripts/parse-coverage.py" ]]; then
        print_info "解析覆盖率数据..."
        cd "$reports_dir"
        python3 "$SCRIPT_DIR/docker/scripts/parse-coverage.py" jacoco.xml
        cd "$SCRIPT_DIR"
    else
        # 简单解析
        local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$reports_dir/jacoco.xml" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
        local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$reports_dir/jacoco.xml" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
        
        if [[ -n "$line_covered" && -n "$line_missed" ]]; then
            local total=$((line_covered + line_missed))
            if [[ $total -gt 0 ]]; then
                local percentage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                print_success "$scan_type 覆盖率: $percentage% ($line_covered/$total 行)"
            else
                print_warning "$scan_type 总行数为0"
            fi
        else
            print_warning "$scan_type 无法提取覆盖率数据"
        fi
    fi
    
    # 检查HTML报告
    if [[ -d "$reports_dir/html" ]]; then
        local html_count=$(find "$reports_dir/html" -name "*.html" | wc -l)
        print_success "$scan_type 生成了 $html_count 个HTML文件"
    else
        print_warning "$scan_type 未生成HTML报告"
    fi
}

# 比较结果
compare_results() {
    echo ""
    echo "🔍 比较扫描结果..."
    
    local docker_xml="$TEST_REPORTS_DIR/docker/jacoco.xml"
    local local_xml="$TEST_REPORTS_DIR/local/jacoco.xml"
    local api_xml="$TEST_REPORTS_DIR/api/jacoco.xml"
    
    echo "| 扫描方式 | XML报告 | 覆盖率 | HTML报告 |"
    echo "|----------|---------|--------|----------|"
    
    for scan_type in "Docker" "本地" "API"; do
        local xml_file=""
        case $scan_type in
            "Docker") xml_file="$docker_xml" ;;
            "本地") xml_file="$local_xml" ;;
            "API") xml_file="$api_xml" ;;
        esac
        
        if [[ -f "$xml_file" ]]; then
            local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$xml_file" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
            local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$xml_file" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
            
            local coverage="N/A"
            if [[ -n "$line_covered" && -n "$line_missed" ]]; then
                local total=$((line_covered + line_missed))
                if [[ $total -gt 0 ]]; then
                    coverage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "计算失败")
                    coverage="${coverage}%"
                fi
            fi
            
            local html_status="❌"
            local html_dir="$(dirname "$xml_file")/html"
            if [[ -d "$html_dir" ]]; then
                html_status="✅"
            fi
            
            echo "| $scan_type | ✅ | $coverage | $html_status |"
        else
            echo "| $scan_type | ❌ | N/A | ❌ |"
        fi
    done
}

# 生成测试报告
generate_report() {
    echo ""
    echo "📋 生成测试报告..."
    
    local report_file="$TEST_REPORTS_DIR/test_summary.md"
    
    cat > "$report_file" << EOF
# JaCoCo 覆盖率测试报告

**测试时间**: $(date)
**测试项目**: $REPO_URL
**提交ID**: $COMMIT_ID

## 测试结果

EOF
    
    # 添加各种扫描结果
    for scan_type in "docker" "local" "api"; do
        local xml_file="$TEST_REPORTS_DIR/$scan_type/jacoco.xml"
        if [[ -f "$xml_file" ]]; then
            echo "### ${scan_type^} 扫描" >> "$report_file"
            echo "- ✅ XML报告已生成" >> "$report_file"
            
            local line_covered=$(grep -o 'type="LINE"[^>]*covered="[0-9]*"' "$xml_file" | grep -o 'covered="[0-9]*"' | cut -d'"' -f2 | head -1)
            local line_missed=$(grep -o 'type="LINE"[^>]*missed="[0-9]*"' "$xml_file" | grep -o 'missed="[0-9]*"' | cut -d'"' -f2 | head -1)
            
            if [[ -n "$line_covered" && -n "$line_missed" ]]; then
                local total=$((line_covered + line_missed))
                if [[ $total -gt 0 ]]; then
                    local coverage=$(echo "scale=2; $line_covered * 100 / $total" | bc 2>/dev/null || echo "0")
                    echo "- 📊 行覆盖率: ${coverage}%" >> "$report_file"
                    echo "- 📈 覆盖行数: $line_covered/$total" >> "$report_file"
                fi
            fi
            
            if [[ -d "$TEST_REPORTS_DIR/$scan_type/html" ]]; then
                echo "- ✅ HTML报告已生成" >> "$report_file"
            fi
            
            echo "" >> "$report_file"
        fi
    done
    
    print_success "测试报告已生成: $report_file"
}

# 主函数
main() {
    print_info "开始 JaCoCo 覆盖率测试..."
    
    # 运行各种测试
    test_docker_scan
    test_local_scan
    test_api_scan
    
    # 比较和分析结果
    compare_results
    generate_report
    
    echo ""
    print_success "测试完成！"
    print_info "测试结果保存在: $TEST_REPORTS_DIR"
    
    # 显示建议
    echo ""
    echo "💡 建议："
    if [[ -f "$TEST_REPORTS_DIR/docker/jacoco.xml" ]]; then
        print_success "Docker 扫描正常工作"
    else
        print_warning "Docker 扫描有问题，请检查镜像构建"
    fi
    
    if [[ -f "$TEST_REPORTS_DIR/local/jacoco.xml" ]]; then
        print_success "本地 Maven 扫描正常工作"
    else
        print_warning "本地 Maven 扫描有问题，请检查 Maven 环境"
    fi
}

# 运行主函数
main "$@"
