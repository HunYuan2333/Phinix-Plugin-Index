#!/usr/bin/env python3
"""Read-only publication admission gate. The publisher still repeats all proof checks."""
import os
from bot import INDEX, GitHub, Rejected, require
from admission import PREFIX, event
import label_admission as labels
import source_updates as updates


def needed(api):
    require(os.environ.get('GITHUB_REPOSITORY') == INDEX and
            os.environ.get('GITHUB_REF') == 'refs/heads/main', 'PublicationContextRejected')
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        return True
    require(os.environ.get('GITHUB_EVENT_NAME') == 'workflow_run', 'PublicationContextRejected')
    title = labels.payload().get('workflow_run', {}).get('display_title')
    if title == updates.TITLE:
        return updates.upstream(api) is not None
    require(isinstance(title, str) and title.startswith('Label admission #'), 'PublicationTriggerRejected')
    run = labels.upstream(api)
    jobs = api.json(PREFIX + '/actions/runs/' + run + '/jobs?per_page=100')
    admit = [job for job in jobs.get('jobs', []) if job.get('name') == 'admit']
    require(len(admit) == 1 and admit[0].get('conclusion') == 'success', 'PublicationTriggerRejected')
    return True


def main():
    try:
        value = needed(GitHub())
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
            output.write('needed=' + str(value).lower() + '\n')
        event('publication.gate', needed=value)
    except (Rejected, OSError, KeyError, TypeError, ValueError) as error:
        event('publication.gate_rejected', reason=str(error))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
