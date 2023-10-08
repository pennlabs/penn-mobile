import json
from collections import defaultdict

from accounts.ipc import authenticated_request
from django.contrib.auth import get_user_model

from portal.models import Poll, PollOption, PollVote, TargetPopulation


User = get_user_model()


def get_user_info(user):
    """Returns Platform user information"""
    # response = authenticated_request(user, "GET", "https://platform.pennlabs.org/accounts/me/")
    # return json.loads(response.content)
    return {
        "pennid": 47673586,
        "first_name": "Arnav",
        "last_name": "Chopra",
        "username": "arnavc",
        "email": "arnavc@wharton.upenn.edu",
        "groups": [
            "employee",
            "student",
            "member"
        ],
        "product_permission": [],
        "user_permissions": [],
        "student": {
            "major": [
                {
                    "id": 192,
                    "name": "Finance, BS",
                    "degree_type": "BACHELORS"
                }
            ],
            "school": [
                {
                    "id": 12,
                    "name": "The Wharton School"
                }
            ],
            "graduation_year": 2025
        },
        "phone_numbers": [],
        "emails": [
            {
                "id": 24213,
                "value": "arnavc@wharton.upenn.edu",
                "primary": True,
                "verified": True
            }
        ],
        "profile_pic": None
    }


def get_user_clubs(user):
    """Returns list of clubs that user is a member of"""
    # response = authenticated_request(user, "GET", "https://pennclubs.com/api/memberships/")
    # res_json = json.loads(response.content)
    # return {"name": res_json["name"], "image": res_json["image_url"], "club_code": club_code}

    # return res_json
    return [
    {
        "club": {
            "accepting_members": False,
            "active": True,
            "address": "",
            "application_required": 5,
            "appointment_needed": False,
            "approved": True,
            "available_virtually": False,
            "code": "pennlabs",
            "email": "contact@pennlabs.org",
            "enables_subscription": True,
            "founded": "2011-09-01",
            "image_url": "https://s3.amazonaws.com/penn.clubs/clubs_small/7afe3fd61b0b4b27893f6583930b01eb.png",
            "is_favorite": True,
            "is_member": 20,
            "is_subscribe": True,
            "recruiting_cycle": 4,
            "name": "Penn Labs",
            "size": 2,
            "subtitle": "The organization that builds your favorite software.",
            "tags": [
                {
                    "id": 2,
                    "name": "Programming"
                },
                {
                    "id": 4,
                    "name": "Technology"
                },
                {
                    "id": 58,
                    "name": "Academic"
                },
                {
                    "id": 70,
                    "name": "Undergraduate"
                },
                {
                    "id": 71,
                    "name": "Graduate"
                }
            ]
        },
        "role": 20,
        "title": "Member",
        "active": True,
        "public": True
    }
]


def get_club_info(user, club_code):
    """Returns club information based on club code"""
    # response = authenticated_request(user, "GET", f"https://pennclubs.com/api/clubs/{club_code}/")
    # res_json = json.loads(response.content)
    # print("HELLO")
    # print(res_json)
    # return {"name": res_json["name"], "image": res_json["image_url"], "club_code": club_code}
    x =  {
    "accepting_members": False,
    "active": True,
    "address": "",
    "application_required": 5,
    "appointment_needed": False,
    "approved": True,
    "available_virtually": False,
    "code": "pennlabs",
    "email": "contact@pennlabs.org",
    "enables_subscription": True,
    "favorite_count": 556,
    "founded": "2011-09-01",
    "image_url": "https://s3.amazonaws.com/penn.clubs/clubs_small/7afe3fd61b0b4b27893f6583930b01eb.png",
    "is_favorite": False,
    "is_member": False,
    "is_subscribe": False,
    "membership_count": 82,
    "recruiting_cycle": 4,
    "name": "Penn Labs",
    "size": 2,
    "subtitle": "The organization that builds your favorite software.",
    "tags": [
        {
            "id": 2,
            "name": "Programming"
        },
        {
            "id": 4,
            "name": "Technology"
        },
        {
            "id": 58,
            "name": "Academic"
        },
        {
            "id": 70,
            "name": "Undergraduate"
        },
        {
            "id": 71,
            "name": "Graduate"
        }
    ],
    "advisor_set": [],
    "approved_by": None,
    "approved_comment": "As a registered undergraduate group, your club is eligible to participate in the annual Fall Activities Fair sponsored by the Student Activities Council(SAC). \n\nThe Fair will be held Aug 29 – 31 from 12p-4p each day. Hosted on College Green & Locust Walk, the Fair will showcase a wide array of student-run clubs, with each day dedicated to highlighting different categories of groups that are active on campus. \n\n The deadline to sign-up for the Fair is Thu, August 24th at 11:59am. \n\nYou can access the SAC Fair Registration Form at https://forms.gle/DLDQXGLXeMSoZKLN7\n\nQuestions can be directed to fair@sacfunded.net.",
    "badges": [],
    "created_at": "2019-09-01T16:50:04.357000-04:00",
    "description": "<p>Watch our previous info session to learn more about Penn Labs:</p>\n<p><a href=\"https://drive.google.com/file/d/19vs_VtoAk5dGS1yNRGlTuoSspLuOpogE/view?usp=sharing\">Spring 2022 Info Session</a> - Recorded January 21, 2022</p>\n<p>Password is: <code>1bT$tt18</code></p>\n<p>We are a team of student software engineers, product designers, and business developers. Our ultimate goal is improving the Penn community with technology. In addition to creating 100% free high-quality products, we give back with educational resources and technical support.</p>\n<img alt=\"undefined\" src=\"https://pennlabs.org/static/416ac117cc2b2327714096edf1937ea1/724c8/labs-group-sp22.jpg\" style=\"\">\n<p></p>",
    "events": [],
    "facebook": "https://facebook.com/labsatpenn/",
    "github": "https://github.com/pennlabs/",
    "how_to_get_involved": "<p>We recruit new members at the beginning of each semester. Join our listserv to learn more when applications are released, as well as incoming info sessions.<br><br>Apply at <a href=\"https://pennclubs.com/club/pennlabs/apply\">https://pennclubs.com/club/pennlabs/apply</a> </p>",
    "instagram": "https://instagram.com/pennlabs/",
    "is_ghost": False,
    "is_request": False,
    "is_wharton": False,
    "linkedin": "https://linkedin.com/company/penn-labs",
    "listserv": "Subscribe on Penn Clubs :D",
    "members": [
        {
            "active": True,
            "email": "cphalen@seas.upenn.edu",
            "image": None,
            "name": "Campbell Phalen",
            "public": True,
            "title": "Director Emeritus",
            "username": "cphalen",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Hassan Hammoud",
            "public": True,
            "title": "Director Emeritus",
            "username": "hammoudh",
            "description": ""
        },
        {
            "active": True,
            "email": "joyliu@wharton.upenn.edu",
            "image": "https://s3.amazonaws.com/penn.clubs/users/joyliu.JPG",
            "name": "Joy Liu",
            "public": True,
            "title": "Co-Director",
            "username": "joyliu",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/5dd018b86ea2462280535bc586f6b429.jpg",
            "name": "Kepler Boonstra",
            "public": True,
            "title": "Co-Director",
            "username": "kboonst",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Rohan Gupta",
            "public": True,
            "title": "Director Emeritus",
            "username": "grohan",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Jessica Tan",
            "public": True,
            "title": "Team Lead",
            "username": "jytan",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Jong Min Choi",
            "public": True,
            "title": "Member",
            "username": "jongmin",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "",
            "public": True,
            "title": "Member",
            "username": "sharkuo",
            "description": ""
        },
        {
            "active": True,
            "email": "aagamd@seas.upenn.edu",
            "image": None,
            "name": "Aagam Dalal",
            "public": True,
            "title": "Member",
            "username": "aagamd",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Adam Strike",
            "public": True,
            "title": "Member",
            "username": "astrike",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Alice He",
            "public": True,
            "title": "Member",
            "username": "healice",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Andrew Antenberg",
            "public": True,
            "title": "Member",
            "username": "aanten",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/3c9a9df5f5a94817baae354823180dee.png",
            "name": "Andy Jiang",
            "public": True,
            "title": "Member",
            "username": "jianga",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Anna Jiang",
            "public": True,
            "title": "Member",
            "username": "annajg",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/annawang.jpg",
            "name": "Anna Wang",
            "public": True,
            "title": "Member",
            "username": "annawang",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/annawang.jpg",
            "name": "Arnav Chopra",
            "public": True,
            "title": "Member",
            "username": "arnavc",
            "description": ""
        },
        {
            "active": True,
            "email": "antli@wharton.upenn.edu",
            "image": "https://s3.amazonaws.com/penn.clubs/users/antli.jpg",
            "name": "Anthony Li",
            "public": True,
            "title": "Member",
            "username": "antli",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Ashley Zhang",
            "public": True,
            "title": "Member",
            "username": "ashzhang",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Baile Chen",
            "public": True,
            "title": "Member",
            "username": "cbaile",
            "description": ""
        },
        {
            "active": True,
            "email": "benxu@seas.upenn.edu",
            "image": None,
            "name": "Benjamin Xu",
            "public": True,
            "title": "Member",
            "username": "benxu",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Brandon Wang",
            "public": True,
            "title": "Member",
            "username": "brandw",
            "description": ""
        },
        {
            "active": True,
            "email": "chuu@seas.upenn.edu",
            "image": None,
            "name": "Christina Qiu",
            "public": True,
            "title": "Member",
            "username": "chuu",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Constance Wang",
            "public": True,
            "title": "Member",
            "username": "conswang",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Daniel Duan",
            "public": True,
            "title": "Member",
            "username": "duaniel",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Daniel Ng",
            "public": True,
            "title": "Member",
            "username": "dng8000",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/2fa92d40dabd4620939387fa7444475f.jpg",
            "name": "Daniel Tao",
            "public": True,
            "title": "Member",
            "username": "dtao",
            "description": ""
        },
        {
            "active": True,
            "email": "dyzhao@seas.upenn.edu",
            "image": None,
            "name": "Daniel Zhao",
            "public": True,
            "title": "Member",
            "username": "dyzhao",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "David Feng",
            "public": True,
            "title": "Member",
            "username": "dfeng678",
            "description": ""
        },
        {
            "active": True,
            "email": "eecho@sas.upenn.edu",
            "image": None,
            "name": "Eecho Yuan",
            "public": True,
            "title": "Member",
            "username": "eecho",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Eric Chen",
            "public": True,
            "title": "Member",
            "username": "ebchen",
            "description": ""
        },
        {
            "active": True,
            "email": "exwang@sas.upenn.edu",
            "image": None,
            "name": "Ethan Wang",
            "public": True,
            "title": "Member",
            "username": "exwang",
            "description": ""
        },
        {
            "active": True,
            "email": "esinx@seas.upenn.edu",
            "image": "https://s3.amazonaws.com/penn.clubs/users/esinx.png",
            "name": "Eunsoo Shin",
            "public": True,
            "title": "Member",
            "username": "esinx",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Eva Killenberg",
            "public": True,
            "title": "Member",
            "username": "evakill",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Gautam Ramesh",
            "public": True,
            "title": "Member",
            "username": "gautam1",
            "description": ""
        },
        {
            "active": True,
            "email": "gbotros@sas.upenn.edu",
            "image": None,
            "name": "George Botros",
            "public": True,
            "title": "Member",
            "username": "gbotros",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Jasmine Cao",
            "public": True,
            "title": "Member",
            "username": "jcao3",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Jefferson Ding",
            "public": True,
            "title": "Member",
            "username": "tyding",
            "description": ""
        },
        {
            "active": True,
            "email": "jxiao23@seas.upenn.edu",
            "image": "https://s3.amazonaws.com/penn.clubs/users/jxiao23.jpg",
            "name": "Jeffrey Xiao",
            "public": True,
            "title": "Member",
            "username": "jxiao23",
            "description": ""
        },
        {
            "active": True,
            "email": "jessez@seas.upenn.edu",
            "image": None,
            "name": "Jesse Zong",
            "public": True,
            "title": "Member",
            "username": "jessez",
            "description": ""
        },
        {
            "active": True,
            "email": "jhawkman@seas.upenn.edu",
            "image": None,
            "name": "Jordan Hochman",
            "public": True,
            "title": "Member",
            "username": "jhawkman",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Justin Lieb",
            "public": True,
            "title": "Member",
            "username": "jtlieb",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Justin Zhang",
            "public": True,
            "title": "Member",
            "username": "judtin",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Karthik Padmanabhan",
            "public": True,
            "title": "Member",
            "username": "ksai",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Kevin Chen",
            "public": True,
            "title": "Member",
            "username": "kevc528",
            "description": ""
        },
        {
            "active": True,
            "email": "kygchng@wharton.upenn.edu",
            "image": None,
            "name": "Kylie Chang",
            "public": True,
            "title": "Member",
            "username": "kygchng",
            "description": ""
        },
        {
            "active": True,
            "email": "lanruo@wharton.upenn.edu",
            "image": "https://s3.amazonaws.com/penn.clubs/users/lanruo.jpg",
            "name": "Laura Gao",
            "public": True,
            "title": "Member",
            "username": "lanruo",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Laurel Lee",
            "public": True,
            "title": "Member",
            "username": "laurlee",
            "description": ""
        },
        {
            "active": True,
            "email": "lstting@seas.upenn.edu",
            "image": None,
            "name": "Linda Ting",
            "public": True,
            "title": "Member",
            "username": "lstting",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Matthew Rosca-Halmagean",
            "public": True,
            "title": "Member",
            "username": "mattrh",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Maximilian Tsiang",
            "public": True,
            "title": "Member",
            "username": "mtsiang",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Michelle Pang",
            "public": True,
            "title": "Member",
            "username": "mipang",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Mohamed Eltigani Osman Abak",
            "public": True,
            "title": "Member",
            "username": "alnasir7",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Nicolas Corona",
            "public": True,
            "title": "Member",
            "username": "njcorona",
            "description": ""
        },
        {
            "active": True,
            "email": "leerache@wharton.upenn.edu",
            "image": None,
            "name": "Rachel Lee",
            "public": True,
            "title": "Member",
            "username": "leerache",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Rafael Marques",
            "public": True,
            "title": "Member",
            "username": "rmarques",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/raunaqs.jpg",
            "name": "Raunaq Singh",
            "public": True,
            "title": "Member",
            "username": "raunaqs",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Rehaan Furniturewala",
            "public": True,
            "title": "Member",
            "username": "rehaan",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Samantha Lee",
            "public": True,
            "title": "Member",
            "username": "smlee18",
            "description": ""
        },
        {
            "active": True,
            "email": "sxd4383@seas.upenn.edu",
            "image": "https://s3.amazonaws.com/penn.clubs/users/sxd4383.JPG",
            "name": "Sherry Xue",
            "public": True,
            "title": "Member",
            "username": "sxd4383",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Sophia Ye",
            "public": True,
            "title": "Member",
            "username": "sophiaye",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/6ee6e690f8074d54851b9867d2f37208.png",
            "name": "Sophie Chen",
            "public": True,
            "title": "Member",
            "username": "sophiech",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": "https://s3.amazonaws.com/penn.clubs/users/6652759738e449569a85574a8dac48e2.jpeg",
            "name": "Tanay Chandak",
            "public": True,
            "title": "Member",
            "username": "tanayc",
            "description": ""
        },
        {
            "active": True,
            "email": "tlshaw@sas.upenn.edu",
            "image": None,
            "name": "Thomas Shaw",
            "public": True,
            "title": "Member",
            "username": "tlshaw",
            "description": ""
        },
        {
            "active": True,
            "email": "trini@seas.upenn.edu",
            "image": None,
            "name": "Trini Feng",
            "public": True,
            "title": "Member",
            "username": "trini",
            "description": ""
        },
        {
            "active": True,
            "email": "tuneer@seas.upenn.edu",
            "image": None,
            "name": "Tuneer Roy",
            "public": True,
            "title": "Member",
            "username": "tuneer",
            "description": ""
        },
        {
            "active": True,
            "email": "vavali@seas.upenn.edu",
            "image": None,
            "name": "Vedha Avali",
            "public": True,
            "title": "Member",
            "username": "vavali",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "William Goeller",
            "public": True,
            "title": "Member",
            "username": "wgoeller",
            "description": ""
        },
        {
            "active": True,
            "email": "willguo6@wharton.upenn.edu",
            "image": None,
            "name": "William Guo",
            "public": True,
            "title": "Member",
            "username": "willguo6",
            "description": ""
        },
        {
            "active": True,
            "email": None,
            "image": None,
            "name": "Anonymous",
            "public": False,
            "title": "Member",
            "username": None,
            "description": ""
        }
    ],
    "signature_events": "",
    "student_types": [],
    "target_majors": [],
    "target_schools": [],
    "target_years": [],
    "testimonials": [
        {
            "id": 184,
            "text": "Penn Labs not only allowed me to meet some of the most talented developers I've ever known, but also helped me grow as a developer through mentorship by those devs! As soon as I joined Labs I was given opportunities to take on real responsibilities organizing and contributing to development behind products used by thousands of Penn students. I would recommend anyone who feels technically ready to apply."
        },
        {
            "id": 186,
            "text": "Penn Labs has become my family. I've gotten to build great products with really talented and passionate people from all kinds of backgrounds, and I never stop learning from them—whether we're in a meeting or just hanging out. I think it's one of the most unique experiences at Penn, because it has cultivated a startup-like environment and is highly professional in everything it does. There's really no limit to what I feel like I can learn or achieve in Labs, and the club has supported me every step of the way."
        }
    ],
    "twitter": None,
    "website": "https://pennlabs.org/",
    "youtube": None
}
    return {"name": x["name"], "image": x["image_url"], "club_code": club_code}


def get_user_populations(user):
    """Returns the target populations that the user belongs to"""

    user_info = get_user_info(user)

    year = (
        [
            TargetPopulation.objects.get(
                kind=TargetPopulation.KIND_YEAR, population=user_info["student"]["graduation_year"]
            )
        ]
        if user_info["student"]["graduation_year"]
        else []
    )

    school = (
        [
            TargetPopulation.objects.get(kind=TargetPopulation.KIND_SCHOOL, population=x["name"])
            for x in user_info["student"]["school"]
        ]
        if user_info["student"]["school"]
        else []
    )

    major = (
        [
            TargetPopulation.objects.get(kind=TargetPopulation.KIND_MAJOR, population=x["name"])
            for x in user_info["student"]["major"]
        ]
        if user_info["student"]["major"]
        else []
    )

    degree = (
        [
            TargetPopulation.objects.get(
                kind=TargetPopulation.KIND_DEGREE, population=x["degree_type"]
            )
            for x in user_info["student"]["major"]
        ]
        if user_info["student"]["major"]
        else []
    )

    return [year, school, major, degree]


def check_targets(obj, user):
    """
    Check if user aligns with target populations of poll or post
    """

    populations = get_user_populations(user)

    year = set(obj.target_populations.filter(kind=TargetPopulation.KIND_YEAR))
    school = set(obj.target_populations.filter(kind=TargetPopulation.KIND_SCHOOL))
    major = set(obj.target_populations.filter(kind=TargetPopulation.KIND_MAJOR))
    degree = set(obj.target_populations.filter(kind=TargetPopulation.KIND_DEGREE))

    return (
        set(populations[0]).issubset(year)
        and set(populations[1]).issubset(school)
        and set(populations[2]).issubset(major)
        and set(populations[3]).issubset(degree)
    )


def get_demographic_breakdown(poll_id):
    """Collects Poll statistics on school and graduation year demographics"""

    # passing in id is necessary because
    # poll info is already serialized
    poll = Poll.objects.get(id=poll_id)
    data = []

    # gets all options for the poll
    options = PollOption.objects.filter(poll=poll)
    for option in options:
        context = {"option": option.choice, "breakdown": defaultdict(lambda: defaultdict(int))}
        # gets all votes for the option
        votes = PollVote.objects.filter(poll_options__in=[option])
        for vote in votes:
            # goes through each vote and adds +1 to the
            # target populations that the voter belongs to
            for target_population in vote.target_populations.all():
                context["breakdown"][target_population.kind][target_population.population] += 1
        data.append(context)
    return data
