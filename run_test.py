import requests
import sys

gid = requests.post('http://localhost:8080/game/2').text
pid = requests.post('http://localhost:8080/game/{}/player/han'.format(gid)).json()['pid']
print('here', pid, gid)
for i in range(10):
    print(requests.post('http://localhost:8080/game/{}/player/{}/draw'.format(gid, pid)).text)
print(requests.get('http://localhost:8080/game/{}/player/{}'.format(gid, pid)).text)

