# Changelog

All notable changes to this project will be documented in this file.

## [1.5.0] - 2025-12-16

### 🎯 NCCN Risk Assessment - Dual Storage Architecture

#### Added
- **RiskAssessment Model** (`app/models/risk_assessment.py`)
  - Structured table for storing NCCN genetic testing criteria assessments
  - Automatic risk scoring (80.00 for high-risk, 20.00 for low-risk)
  - Risk categorization ("high", "moderate", "low")
  - JSONB details field with full assessment data and session linkage
  - Factory method `from_nccn_assessment()` for creating from chat sessions

- **RiskAssessmentRepository** (`app/repositories/risk_assessment_repository.py`)
  - CRUD operations for risk assessments
  - Analytics queries: `get_high_risk_patients()`, `get_by_patient()`, `get_latest_by_patient()`
  - Support for filtering by assessment type and date ranges

- **Dual Storage Implementation** (`app/services/ai_chat_engine.py`)
  - Assessments stored in TWO locations:
    1. `ai_chat_sessions.assessment_results` (JSON) - for quick session access
    2. `risk_assessments` table (structured) - for analytics and reporting
  - Graceful error handling - session continues even if analytics storage fails
  - Session linkage via `details.session_id` in risk_assessments table

- **Session Auto-Completion**
  - Sessions automatically marked as "completed" when NCCN criteria is met
  - `completed_at` timestamp recorded
  - Assessment results persisted before completion

#### Enhanced
- **Assessment Retrieval** (`ai_chat_engine.py:282-301`)
  - Implemented `get_session_assessment()` method
  - Returns stored assessment from `ai_chat_sessions.assessment_results`
  - Available via API endpoint: `GET /ai-chat/sessions/{id}/assessment`

- **Patient Model** (`app/models/patient.py`)
  - Added relationship: `risk_assessments` with cascade delete
  - Enables querying patient risk history

#### Testing
- End-to-end tests verified all features working:
  - ✅ NCCN criteria assessment (breast cancer at age ≤45)
  - ✅ Assessment persistence in both storage locations
  - ✅ Session auto-completion when criteria met
  - ✅ Risk score calculation (80.00 for high risk)
  - ✅ Session-to-assessment traceability

#### Use Cases Enabled
1. **Real-time Access**: Get assessment from active session context
2. **Analytics Dashboard**: Query all high-risk patients across sessions
3. **Patient History**: View assessment trends over time per patient
4. **Audit Trail**: Trace assessments back to originating conversations

#### Database Changes
- New table: `risk_assessments`
- Foreign keys: `patient_id` → `patients.id`, `assessed_by` → `users.id`
- Indexes: `patient_id`, `assessment_type`, `created_at` for optimal query performance

#### Documentation Updates
- **NCCN_RAG_IMPLEMENTATION.md**: Comprehensive documentation of dual storage architecture
  - Storage locations and purposes
  - Database schemas and examples
  - Analytics queries
  - Use cases and deployment status

#### Technical Details
- **Commits**: aed8a2c (SQLAlchemy model registration fix)
- **Deployment**: 2025-12-16
- **Image Digest**: `sha256:6d9b8fa6d876742d95b6a1de7c6af95ca93fb2b4be198c82fed789aaeb429012`
- **Status**: Production-ready, all tests passing

## [Unreleased] - 2025-08-17

### 🚀 Added
- **Docker Build Optimization**: Comprehensive Docker build improvements
  - Multi-stage build architecture for optimized image size and caching
  - Build script automation (`build.sh`) for development and production builds
  - Enhanced `.dockerignore` for better build context optimization
  - Docker Compose override for development workflow with hot-reload
  - Security hardening with non-root user execution
  - Virtual environment isolation for better dependency management

### 📈 Performance Improvements
- **75% faster Docker builds** (2-3 minutes vs 8-12 minutes)
- **14% smaller image size** (1.6GB vs 1.86GB)
- **80% smaller build context** through optimized `.dockerignore`
- Better layer caching and dependency management

### 🔧 Developer Experience
- Automated build scripts for consistent development workflow
- Hot-reload support in development mode
- Enhanced development setup documentation
- Streamlined CI/CD pipeline with optimized builds

### 📚 Documentation Updates
- Updated `README.md` with Docker-first development approach
- Enhanced `DEPLOYMENT.md` with Docker optimization benefits
- Improved `DEVELOPMENT_SETUP.md` with quick-start Docker commands
- Comprehensive `DOCKER_OPTIMIZATION.md` with performance metrics
- Updated CI/CD workflow to use optimized build scripts

### 🛠️ Technical Changes
- **Dockerfile**: Complete rewrite with multi-stage build
- **build.sh**: New automated build script with environment detection
- **docker-compose.override.yml**: Development-specific configurations
- **.dockerignore**: Enhanced exclusions for optimal build performance
- **CI/CD**: Updated GitHub Actions to use optimized build process

### 🔐 Security Enhancements
- Non-root user execution in Docker containers
- Minimal attack surface with python:3.11-slim base image
- Proper file permissions and ownership
- Virtual environment isolation
