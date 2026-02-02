#!/bin/bash
# version.sh - 버전 관리 헬퍼 (Enhanced)
# Usage: ./scripts/version.sh <project-name> <type> [action] [args]
# Types: images, videos
# Actions: list, new, select, rollback, compare

set -e

PROJECT_NAME=$1
TYPE=$2
ACTION=${3:-list}
ARG1=$4
ARG2=$5

if [ -z "$PROJECT_NAME" ] || [ -z "$TYPE" ]; then
    echo "🛡️ Version Control Helper v2.0"
    echo ""
    echo "Usage: ./scripts/version.sh <project-name> <type> [action] [args]"
    echo ""
    echo "   Types: images, videos"
    echo "   Actions:"
    echo "      list              - 모든 버전 목록"
    echo "      new               - 새 버전 생성"
    echo "      select <ver>      - 버전 전체를 selected/로"
    echo "      rollback <ver>    - 해당 버전으로 롤백"
    echo "      compare <v1> <v2> - 두 버전 비교"
    echo ""
    echo "   Examples:"
    echo "   ./scripts/version.sh kylenutt-parody images list"
    echo "   ./scripts/version.sh kylenutt-parody images new"
    echo "   ./scripts/version.sh kylenutt-parody images rollback v1"
    echo "   ./scripts/version.sh kylenutt-parody images compare v1 v2"
    exit 1
fi

BASE_DIR="/Users/ted/viral-video-automation"
PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"

case $TYPE in
    image|images)
        GENERATED_DIR="$PROJECT_DIR/generated/images"
        ;;
    video|videos)
        GENERATED_DIR="$PROJECT_DIR/generated/videos"
        ;;
    *)
        echo "❌ Invalid type: $TYPE (use: images, videos)"
        exit 1
        ;;
esac

# 메타데이터 생성 함수
create_metadata() {
    local VER_DIR=$1
    local VER_NAME=$2
    local NOTES=${3:-""}
    
    cat > "$VER_DIR/_metadata.json" << EOF
{
  "version": "$VER_NAME",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status": "active",
  "notes": "$NOTES",
  "files": [$(ls "$VER_DIR" 2>/dev/null | grep -v "_metadata" | sed 's/^/"/;s/$/"/' | tr '\n' ',' | sed 's/,$//' || echo "")]
}
EOF
}

case $ACTION in
    list)
        echo "📁 Versions for $TYPE in $PROJECT_NAME:"
        echo ""
        for ver_dir in "$GENERATED_DIR"/v*; do
            if [ -d "$ver_dir" ]; then
                ver=$(basename $ver_dir)
                count=$(ls "$ver_dir" 2>/dev/null | grep -v "_metadata" | wc -l | tr -d ' ')
                notes=""
                if [ -f "$ver_dir/_metadata.json" ]; then
                    notes=$(grep '"notes"' "$ver_dir/_metadata.json" 2>/dev/null | cut -d'"' -f4 || echo "")
                fi
                echo "   $ver: $count files ${notes:+- $notes}"
            fi
        done
        echo ""
        if [ -d "$GENERATED_DIR/selected" ]; then
            count=$(ls "$GENERATED_DIR/selected" 2>/dev/null | grep -v "_version" | wc -l | tr -d ' ')
            echo "   selected/: $count files"
        fi
        ;;
    
    new)
        # 다음 버전 번호 찾기
        NEXT_VER=1
        while [ -d "$GENERATED_DIR/v$NEXT_VER" ]; do
            NEXT_VER=$((NEXT_VER + 1))
        done
        
        mkdir -p "$GENERATED_DIR/v$NEXT_VER"
        create_metadata "$GENERATED_DIR/v$NEXT_VER" "v$NEXT_VER" "Created"
        
        echo "✅ Created: v$NEXT_VER"
        echo "📁 Path: $GENERATED_DIR/v$NEXT_VER/"
        echo ""
        echo "📋 Next: Copy your generated files to this directory"
        ;;
    
    select)
        if [ -z "$ARG1" ]; then
            echo "❌ Usage: ./scripts/version.sh $PROJECT_NAME $TYPE select <version>"
            exit 1
        fi
        
        SRC_DIR="$GENERATED_DIR/$ARG1"
        if [ ! -d "$SRC_DIR" ]; then
            echo "❌ Version not found: $ARG1"
            exit 1
        fi
        
        mkdir -p "$GENERATED_DIR/selected"
        
        # 기존 selected 백업
        if [ "$(ls -A $GENERATED_DIR/selected 2>/dev/null)" ]; then
            BACKUP_NAME="_backup_$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$GENERATED_DIR/$BACKUP_NAME"
            cp -r "$GENERATED_DIR/selected/"* "$GENERATED_DIR/$BACKUP_NAME/"
            echo "📦 Backup: selected/ → $BACKUP_NAME/"
        fi
        
        # 복사
        cp "$SRC_DIR"/* "$GENERATED_DIR/selected/" 2>/dev/null || true
        
        # _version.json 생성
        echo "{\"from\": \"$ARG1\", \"selected_at\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > "$GENERATED_DIR/selected/_version.json"
        
        echo "✅ Selected: $ARG1 → selected/"
        ;;
    
    rollback)
        if [ -z "$ARG1" ]; then
            echo "❌ Usage: ./scripts/version.sh $PROJECT_NAME $TYPE rollback <version>"
            exit 1
        fi
        
        SRC_DIR="$GENERATED_DIR/$ARG1"
        if [ ! -d "$SRC_DIR" ]; then
            echo "❌ Version not found: $ARG1"
            exit 1
        fi
        
        echo "🔄 Rolling back to $ARG1..."
        
        # 기존 selected 백업
        mkdir -p "$GENERATED_DIR/selected"
        if [ "$(ls -A $GENERATED_DIR/selected 2>/dev/null)" ]; then
            BACKUP_NAME="_rollback_backup_$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$GENERATED_DIR/$BACKUP_NAME"
            cp -r "$GENERATED_DIR/selected/"* "$GENERATED_DIR/$BACKUP_NAME/"
            echo "📦 Backup: selected/ → $BACKUP_NAME/"
        fi
        
        # 롤백
        rm -rf "$GENERATED_DIR/selected/"*
        cp "$SRC_DIR"/* "$GENERATED_DIR/selected/" 2>/dev/null || true
        
        # _version.json 업데이트
        echo "{\"from\": \"$ARG1\", \"rollback_at\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > "$GENERATED_DIR/selected/_version.json"
        
        echo "✅ Rollback complete: $ARG1 → selected/"
        ;;
    
    compare)
        if [ -z "$ARG1" ] || [ -z "$ARG2" ]; then
            echo "❌ Usage: ./scripts/version.sh $PROJECT_NAME $TYPE compare <v1> <v2>"
            exit 1
        fi
        
        DIR1="$GENERATED_DIR/$ARG1"
        DIR2="$GENERATED_DIR/$ARG2"
        
        if [ ! -d "$DIR1" ]; then
            echo "❌ Version not found: $ARG1"
            exit 1
        fi
        if [ ! -d "$DIR2" ]; then
            echo "❌ Version not found: $ARG2"
            exit 1
        fi
        
        echo "📊 Comparing $ARG1 vs $ARG2:"
        echo ""
        echo "Files in $ARG1:"
        ls -la "$DIR1" | grep -v "_metadata"
        echo ""
        echo "Files in $ARG2:"
        ls -la "$DIR2" | grep -v "_metadata"
        echo ""
        
        # 파일 개수 비교
        COUNT1=$(ls "$DIR1" 2>/dev/null | grep -v "_metadata" | wc -l | tr -d ' ')
        COUNT2=$(ls "$DIR2" 2>/dev/null | grep -v "_metadata" | wc -l | tr -d ' ')
        echo "Summary: $ARG1 has $COUNT1 files, $ARG2 has $COUNT2 files"
        ;;
    
    *)
        echo "❌ Invalid action: $ACTION"
        echo "   Valid actions: list, new, select, rollback, compare"
        exit 1
        ;;
esac

