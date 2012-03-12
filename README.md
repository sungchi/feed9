FEED9
=====

Feed9은 공유하는 링크들의 주소를 줄이고, 클릭횟수를 확인하고, 공유한 링크들을 관리하기 위해 만들어졌습니다. 누구나 회원가입해서 다른 사람의 링크를 보고 점수를 줄 수 있습니다.

회원가입 후에 제목(필수),링크,카테고리를 입력해서 링크를 올릴 수 있습니다. 각각의 링크는 Feed9의 주소가 부여되는데 그 주소를 짧은 주소로 이용해 외부에 공유하면 클릭 숫자가 집계됩니다.

Feed9은 "투자와 인맥으로부터 자유로운 인디 웹서비스"입니다.(강제로 자유)

카테고리 신청, 피드백
---------------------

admin@feed9.com, <a href="http://twitter.com/sungchi">@sungchi</a>

web2py 소스 수정(이 저장소에는 web2py 소스가 없습니다):

1. gae_google_account.py : 사용자 model에 맞춰서 수정
2. routes.py : fancy URL 추가
3. gluon/tools.py : cas.get_user() 아랫부분 수정  