import pathlib

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    # 필수 항목
    name="joywins_my_data_coupang_order",  # PyPI에서 유일한 패키지 이름
    version="0.0.2",           # 버전 번호 (e.g., "1.0.0", "0.1.2")
    author="joywins123",        # 작성자 이름
    author_email="joywins123@gmail.com",  # 연락 가능한 이메일
    description="쿠팡 주문 목록 스크래퍼",  # 한 줄 설명
    # long_description=long_description,  # README 파일의 내용
    long_description=pathlib.Path("README.md").read_text(encoding="utf-8"),  # README 파일의 내용
    long_description_content_type="text/markdown",  # README 파일 형식
    url="https://github.com/JoyWins123/joywins_my_data_coupang_order",  # 소스코드 저장소 URL
    
    # 선택적 항목들
    packages=setuptools.find_packages(),  # 자동으로 모든 파이썬 패키지를 찾음
    include_package_data=True,  # 패키지 데이터를 포함
    
    # entry_points = {"console_scripts": ["a = a.cli:main"]},
    
    classifiers=[
        "Development Status :: 3 - Alpha",  # 개발 상태
        "Intended Audience :: Developers",  # 대상 사용자
        "Programming Language :: Python :: 3.8",  # 지원하는 파이썬 버전
        "License :: OSI Approved :: MIT License",  # 라이선스
        "Operating System :: OS Independent",  # 지원하는 운영체제
    ],
    python_requires=">=3.8",  # 필요한 최소 파이썬 버전
    
    # 선택적: 패키지 의존성 명시
    # install_requires=[
    #     # "requests>=2.22.0",  # 필요한 외부 패키지
    # ],
    
    # 선택적: 프로젝트 키워드
    # keywords="sample, package, setup",
    
    # 선택적: 프로젝트 홈페이지
    project_urls={
        # "Bug Tracker": "https://github.com/yourusername/yourrepository/issues",
        # "Documentation": "https://yourpackage.readthedocs.io/",
        "Source Code": "https://github.com/JoyWins123/joywins_my_data_coupang_order"  # 프로젝트 홈페이지
    },
)