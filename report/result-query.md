# Issue Resolution Report

        **Generated on:** 2025-09-23 20:32:56

        ## 🎯 Issue
        ISSUE-2: 데이터 영속성 문제

        ## 📁 Relevant Files (5)
        - ./temp_repo/README.md
- ./temp_repo/README.md
- ./temp_repo/README.md
- ./temp_repo/README.md
- ./temp_repo/README.md

## 🤖 Solution
1. 문제 분석
    - 데이터 영속성 문제: 서버 재시작 시 모든 이슈 데이터가 손실되는 문제가 발생하고 있습니다. 이는 데이터베이스를 사용하지 않고, 메모리에 데이터를 저장하고 있기 때문입니다.
    - 동시성 문제: 다중 요청이 발생할 때 ID가 중복 생성되는 문제가 발생하고 있습니다. 이는 단순 카운터를 사용하여 ID를 생성하고 있기 때문입니다.

2. 원인 파악
    - 데이터 영속성 문제: In-memory 저장소를 사용하고 있으며, 데이터베이스와 연동이 되어 있지 않아서 발생하는 문제입니다.
    - 동시성 문제: `AtomicLong`을 사용하지 않고, 단순 카운터를 사용하여 ID를 생성하고 있어서 발생하는 문제입니다.

3. 해결 방안
    - 데이터 영속성 문제: 데이터베이스를 도입하고, Spring Data JPA를 사용하여 데이터를 영속화합니다. H2 데이터베이스를 개발용으로 연동하고, Entity와 Repository를 구현하여 데이터 접근을 처리합니다.
    - 동시성 문제: 동시성을 보장하는 ID 생성 방식을 도입합니다. `AtomicLong` 또는 UUID를 사용하여 ID를 생성하여 동시성 문제를 해결합니다.

4. 코드 예시
```kotlin
import org.springframework.data.jpa.repository.JpaRepository
import javax.persistence.Entity
import javax.persistence.GeneratedValue
import javax.persistence.Id
import java.util.UUID

@Entity
data class Issue(
    @Id @GeneratedValue
    val id: UUID = UUID.randomUUID(),
    var title: String,
    var description: String
)

interface IssueRepository : JpaRepository<Issue, UUID>

@Service
class IssueService(private val issueRepository: IssueRepository) {

    fun getAllIssues(): MutableList<Issue> {
        return issueRepository.findAll()
    }

    fun createIssue(issue: Issue): Issue {
        return issueRepository.save(issue)
    }

    fun getIssueById(id: UUID): Issue {
        return issueRepository.findById(id).orElseThrow { NoSuchElementException("Issue not found") }
    }
}
```

5. 추가 권장사항
    - 테스트 케이스를 작성하여 시스템의 정상 동작을 검증해보는 것이 좋습니다.
    - 문제가 발생할 수 있는 부분에 대해 예외 처리를 구현하고, 사용자에게 적절한 에러 메세지를 제공해주는 것이 중요합니다.
    - 프로덕션 환경에 배포하기 위해서는 실제 사용할 데이터베이스를 연동하고, 컨테이너화를 지원하도록 Dockerfile을 작성하는 것이 필요합니다.

## 🌐 External Research
Research Summary: To solve data persistence issues in Spring Boot with Kotlin, use JPA annotations like @NonNull and @Nullable for null safety. Ensure proper entity mapping and use repositories for data access. Validate and handle exceptions effectively.

Result 1:
Title: Spring Boot,JPA,Kotlin을 사용하며 생긴 이슈 - velog
Content: 회사에서 spring, kotlin,jpa를 사용하면서 발생한 이슈와 해결 방법 등을 공유하겠습니다. 코드는 제가 작성한 극단적인 예시 코드입니다.
URL: https://velog.io/@conatuseus/Spring-BootJPAKotlin%EC%9D%84-%EC%82%AC%EC%9A%A9%ED%95%98%EB%A9%B0-%EC%83%9D%EA%B8%B4-%EC%9D%B4%EC%8A%88

Result 2:
Title: Spring Boot & JPA에서 Java와 Kotlin을 함께 사용하기 - 기술블로그
Content: 여러 모듈이 참조하는 공통 모듈이기 때문에 Spring과 같은 외부 패키지에 최대한 의존하지 않는 것이 좋다고 생각했습니다.

... (more research results available)